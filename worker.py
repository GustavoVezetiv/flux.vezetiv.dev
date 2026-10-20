from __future__ import annotations
import argparse, json, sys, traceback
from models import ImobiPackage
from storage import init_db, connect, set_control, log
from automation.runner import execute_item, StopRequested


def main(package_id: int, dry_run: bool):
    init_db()
    with connect() as con:
        pkg_row = con.execute("SELECT * FROM packages WHERE id=?", (package_id,)).fetchone()
        if not pkg_row:
            raise SystemExit(f"Pacote {package_id} não encontrado")
        pkg = ImobiPackage.model_validate(json.loads(pkg_row["raw_json"]))
        rows = con.execute("SELECT * FROM items WHERE package_id=? AND approved=1 ORDER BY id", (package_id,)).fetchall()
        by_key = {x.id: x for x in pkg.items}

    set_control(worker_status="running", pause_requested=0, stop_requested=0, message="Execução iniciada")
    try:
        for row in rows:
            item = by_key[row["item_key"]]
            with connect() as con:
                con.execute("UPDATE items SET status='running', message=? WHERE id=?", ("Executando", row["id"]))
            set_control(current_item_id=row["id"], worker_status="running", message=f"Executando {item.title}")
            try:
                result = execute_item(dict(row), item, dry_run=dry_run)
                status = "dry_run_ok" if result.get("dry_run") else "done"
                msg = "Simulação concluída" if result.get("dry_run") else "Executado e auditado"
                with connect() as con:
                    con.execute("UPDATE items SET status=?, message=? WHERE id=?", (status, msg, row["id"]))
            except StopRequested:
                with connect() as con:
                    con.execute("UPDATE items SET status='stopped', message='Interrompido pelo operador' WHERE id=?", (row["id"],))
                raise
            except Exception as exc:
                log(f"Erro: {exc}\n{traceback.format_exc()}", "ERROR", row["id"])
                with connect() as con:
                    con.execute("UPDATE items SET status='error', message=? WHERE id=?", (str(exc), row["id"]))
        set_control(worker_status="finished", current_item_id=None, message="Execução concluída")
    except StopRequested:
        set_control(worker_status="stopped", current_item_id=None, message="Execução interrompida")
    except Exception as exc:
        log(f"Falha geral: {exc}\n{traceback.format_exc()}", "ERROR")
        set_control(worker_status="error", current_item_id=None, message=str(exc))

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--package-id", type=int, required=True)
    ap.add_argument("--dry-run", action="store_true")
    ns = ap.parse_args()
    main(ns.package_id, ns.dry_run)
