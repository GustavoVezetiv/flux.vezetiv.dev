from __future__ import annotations
import time
from pathlib import Path
from playwright.sync_api import sync_playwright
from automation.adapter import ImobiBrasilAdapter, LocatorError
from automation.config import load_app_config, load_selectors
from storage import get_control, set_control, log

class StopRequested(Exception):
    pass

def wait_if_paused(message="Controle manual ativo"):
    while True:
        ctrl = get_control()
        if ctrl["stop_requested"]:
            raise StopRequested()
        if not ctrl["pause_requested"]:
            return
        set_control(worker_status="manual_pause", message=message)
        time.sleep(0.6)

def wait_for_operator(message: str, item_id: int):
    log(message, "WARN", item_id)
    set_control(pause_requested=1, worker_status="manual_pause", message=message, current_item_id=item_id)
    wait_if_paused(message)

def execute_item(item_db: dict, item_model, dry_run: bool = True):
    """Executa um item. No modo inicial, a navegação até a Ref. é manual.

    Isto é proposital: permite começar sem depender ainda dos seletores da tela
    de listagem do ImobiBrasil. Depois automatizamos a busca por referência.
    """
    cfg = load_app_config()
    selectors = load_selectors()
    item_id = item_db["id"]
    reference = item_model.reference or "NOVA"

    if dry_run:
        log(f"DRY-RUN {reference}: {len(item_model.changes)} alteração(ões) seriam executadas.", item_id=item_id)
        for ch in item_model.changes:
            log(f"DRY-RUN campo {ch.field}: {ch.old!r} -> {ch.new!r}", item_id=item_id)
        if item_model.private_notes:
            log("DRY-RUN: Dados Privativos seriam atualizados.", item_id=item_id)
        return {"ok": True, "dry_run": True}

    with sync_playwright() as p:
        user_data_dir = Path(cfg.get("user_data_dir", "data/browser-profile"))
        user_data_dir.mkdir(parents=True, exist_ok=True)
        browser = p.chromium.launch_persistent_context(
            user_data_dir=str(user_data_dir),
            headless=False,
            channel=cfg.get("browser_channel") or None,
            viewport=None,
            args=["--start-maximized"],
        )
        page = browser.pages[0] if browser.pages else browser.new_page()
        if cfg.get("start_url"):
            page.goto(cfg["start_url"], wait_until="domcontentloaded")

        # MVP: operador abre a referência correta e depois libera a automação.
        wait_for_operator(
            f"Abra manualmente no ImobiBrasil a Ref. {reference} ({item_model.title}) e clique em CONTINUAR no painel.",
            item_id,
        )

        adapter = ImobiBrasilAdapter(page, selectors)
        for ch in item_model.changes:
            wait_if_paused()
            if ch.requires_manual:
                wait_for_operator(f"Preencha manualmente '{ch.label}' para a Ref. {reference} e clique CONTINUAR.", item_id)
                continue
            try:
                adapter.fill(ch.field, ch.new)
                log(f"Preenchido {ch.label}: {ch.new}", item_id=item_id)
            except LocatorError as exc:
                wait_for_operator(f"{exc}. Preencha esse campo manualmente e clique CONTINUAR.", item_id)

        if item_model.private_notes:
            try:
                adapter.fill("private_notes", item_model.private_notes)
                log("Dados Privativos preenchidos.", item_id=item_id)
            except LocatorError as exc:
                wait_for_operator(f"{exc}. Cole os Dados Privativos manualmente e clique CONTINUAR.", item_id)

        wait_if_paused()
        try:
            adapter.save()
            log("Clique em Salvar executado.", item_id=item_id)
        except LocatorError as exc:
            wait_for_operator(f"{exc}. Salve manualmente e clique CONTINUAR.", item_id)

        page.wait_for_timeout(1000)
        # Auditoria leve: tenta reler apenas os campos alterados.
        mismatches = []
        for ch in item_model.changes:
            if ch.requires_manual:
                continue
            try:
                actual = adapter.read(ch.field)
                expected = "" if ch.new is None else str(ch.new)
                if actual.strip() != expected.strip():
                    mismatches.append((ch.label, expected, actual))
            except Exception:
                pass

        if mismatches:
            for label, expected, actual in mismatches:
                log(f"AUDITORIA: {label} esperado={expected!r}, encontrado={actual!r}", "WARN", item_id)
            wait_for_operator("Auditoria encontrou divergência. Revise a Ref. no navegador e clique CONTINUAR.", item_id)

        browser.close()
        return {"ok": True, "dry_run": False, "mismatches": mismatches}
