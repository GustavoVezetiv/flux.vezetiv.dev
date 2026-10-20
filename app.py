from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
import pandas as pd
import streamlit as st

from models import ImobiPackage
from package_io import load_package_bytes
from storage import init_db, connect, get_control, set_control, list_logs

st.set_page_config(page_title="IMOBI Automation", page_icon="🏠", layout="wide")
init_db()

st.title("🏠 IMOBI Automation — MVP")
st.caption("Revisar → aprovar → executar no navegador → auditar. O robô não decide: ele executa o que foi aprovado.")

with st.sidebar:
    st.subheader("Controle")
    ctrl = get_control()
    st.metric("Worker", ctrl["worker_status"])
    if ctrl.get("message"):
        st.info(ctrl["message"])
    c1, c2 = st.columns(2)
    with c1:
        if st.button("🖱️ Pausar / assumir controle", use_container_width=True):
            set_control(pause_requested=1, message="Controle manual solicitado")
            st.rerun()
    with c2:
        if st.button("▶ Continuar", use_container_width=True):
            set_control(pause_requested=0, message="Continuando automação")
            st.rerun()
    if st.button("⛔ Parar execução", use_container_width=True):
        set_control(stop_requested=1, pause_requested=0, message="Parada solicitada")
        st.rerun()
    st.divider()
    dry_run = st.toggle("Modo simulação (recomendado no início)", value=True)

upload_tab, review_tab, run_tab, history_tab = st.tabs(["📦 Pacote", "✅ Revisão", "▶ Execução", "📜 Histórico"])

with upload_tab:
    st.subheader("Carregar pacote gerado pelo ChatGPT")
    uploaded = st.file_uploader("Arquivo .json", type=["json"])
    if uploaded:
        try:
            pkg = load_package_bytes(uploaded.getvalue())
            st.success(f"Pacote válido: {pkg.name} — {len(pkg.items)} item(ns)")
            st.json(pkg.model_dump(mode="json", exclude_none=True), expanded=False)
            if st.button("Importar pacote"):
                raw = uploaded.getvalue().decode("utf-8")
                with connect() as con:
                    cur = con.execute("INSERT INTO packages(name,source_name,created_at,raw_json) VALUES (?,?,?,?)",
                                      (pkg.name, pkg.source_name, pkg.created_at, raw))
                    pid = cur.lastrowid
                    for item in pkg.items:
                        con.execute("INSERT INTO items(package_id,item_key,reference,title,action,approved,status) VALUES (?,?,?,?,?,?,?)",
                                    (pid, item.id, item.reference, item.title, item.action, int(item.approved), "pending"))
                st.session_state["package_id"] = pid
                st.success(f"Importado como pacote #{pid}")
                st.rerun()
        except Exception as exc:
            st.error(f"Pacote inválido: {exc}")

    with connect() as con:
        pkgs = [dict(r) for r in con.execute("SELECT id,name,source_name,created_at FROM packages ORDER BY id DESC LIMIT 20").fetchall()]
    if pkgs:
        st.dataframe(pd.DataFrame(pkgs), use_container_width=True, hide_index=True)
        ids = [p["id"] for p in pkgs]
        default = st.session_state.get("package_id", ids[0])
        chosen = st.selectbox("Pacote ativo", ids, index=ids.index(default) if default in ids else 0,
                              format_func=lambda x: next(p["name"] for p in pkgs if p["id"]==x))
        st.session_state["package_id"] = chosen

with review_tab:
    pid = st.session_state.get("package_id")
    if not pid:
        st.info("Importe ou selecione um pacote primeiro.")
    else:
        with connect() as con:
            pkg_row = con.execute("SELECT * FROM packages WHERE id=?", (pid,)).fetchone()
            rows = [dict(r) for r in con.execute("SELECT * FROM items WHERE package_id=? ORDER BY id", (pid,)).fetchall()]
        pkg = ImobiPackage.model_validate(json.loads(pkg_row["raw_json"]))
        by_key = {i.id:i for i in pkg.items}
        st.subheader(pkg.name)
        for row in rows:
            item = by_key[row["item_key"]]
            with st.container(border=True):
                left, right = st.columns([4,1])
                with left:
                    st.markdown(f"### {item.title}")
                    st.caption(f"Ref.: {item.reference or 'NOVA'} • Ação: {item.action} • Status: {row['status']}")
                with right:
                    approved = st.checkbox("Aprovado", value=bool(row["approved"]), key=f"ap_{row['id']}")
                    if approved != bool(row["approved"]):
                        with connect() as con:
                            con.execute("UPDATE items SET approved=? WHERE id=?", (int(approved), row["id"]))
                if item.changes:
                    data = [{"Seção":c.section or "", "Campo":c.label, "Atual":c.old, "Novo":c.new, "Manual":c.requires_manual} for c in item.changes]
                    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
                if item.private_notes:
                    with st.expander("Dados Privativos"):
                        st.code(item.private_notes, language=None)
                if item.operator_notes:
                    st.warning(item.operator_notes)

with run_tab:
    pid = st.session_state.get("package_id")
    if not pid:
        st.info("Selecione um pacote primeiro.")
    else:
        with connect() as con:
            rows = [dict(r) for r in con.execute("SELECT * FROM items WHERE package_id=? ORDER BY id", (pid,)).fetchall()]
        approved_count = sum(r["approved"] for r in rows)
        st.subheader(f"Pacote #{pid} — {approved_count} aprovado(s)")
        if approved_count == 0:
            st.warning("Nenhum item aprovado.")
        cols = st.columns([1,1,2])
        with cols[0]:
            if st.button("▶ Iniciar execução", disabled=approved_count==0, use_container_width=True):
                set_control(pause_requested=0, stop_requested=0, worker_status="starting", message="Iniciando worker")
                cmd = [sys.executable, "worker.py", "--package-id", str(pid)]
                if dry_run:
                    cmd.append("--dry-run")
                subprocess.Popen(cmd, cwd=str(Path.cwd()), creationflags=getattr(subprocess, "CREATE_NEW_CONSOLE", 0))
                st.success("Worker iniciado. Use Atualizar status.")
        with cols[1]:
            if st.button("🔄 Atualizar status", use_container_width=True):
                st.rerun()
        st.dataframe(pd.DataFrame(rows)[["reference","title","action","approved","status","message"]], use_container_width=True, hide_index=True)
        st.caption("No primeiro MVP, ao executar de verdade o navegador abre e pede que você navegue manualmente até a Ref.; depois o robô preenche os campos aprovados. A busca automática por Ref. será a próxima etapa.")

with history_tab:
    logs = list_logs(300)
    if logs:
        st.dataframe(pd.DataFrame(logs), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhum log ainda.")
