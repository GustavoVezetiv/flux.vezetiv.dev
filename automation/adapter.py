from __future__ import annotations
from typing import Any
from playwright.sync_api import Page

class LocatorError(RuntimeError):
    pass

class ImobiBrasilAdapter:
    """Camada isolada da interface do ImobiBrasil.

    O MVP começa com navegação manual por Ref. e preenchimento automático da tela
    já aberta. Quando mapearmos a busca/listagem do CRM, esta classe passa a abrir
    a Ref. sozinha sem alterar o restante do sistema.
    """

    def __init__(self, page: Page, selectors: dict):
        self.page = page
        self.selectors = selectors

    def _locator(self, field: str):
        cfg = self.selectors.get("fields", {}).get(field)
        if not cfg:
            raise LocatorError(f"Campo lógico sem mapeamento: {field}")
        if cfg.get("css"):
            return self.page.locator(cfg["css"]).first
        if cfg.get("label"):
            return self.page.get_by_label(cfg["label"], exact=False).first
        if cfg.get("placeholder"):
            return self.page.get_by_placeholder(cfg["placeholder"], exact=False).first
        raise LocatorError(f"Mapeamento incompleto para {field}")

    def fill(self, field: str, value: Any):
        loc = self._locator(field)
        if loc.count() == 0:
            raise LocatorError(f"Não encontrei o campo '{field}' na tela atual")
        text = "" if value is None else str(value)
        tag = loc.evaluate("el => el.tagName.toLowerCase()")
        if tag == "select":
            try:
                loc.select_option(label=text)
            except Exception:
                loc.select_option(value=text)
        else:
            loc.fill(text)

    def read(self, field: str):
        loc = self._locator(field)
        if loc.count() == 0:
            raise LocatorError(f"Não encontrei o campo '{field}' para auditoria")
        tag = loc.evaluate("el => el.tagName.toLowerCase()")
        if tag in ("input", "textarea", "select"):
            return loc.input_value()
        return loc.inner_text()

    def save(self):
        cfg = self.selectors.get("actions", {}).get("save", {})
        if cfg.get("css"):
            self.page.locator(cfg["css"]).first.click()
            return
        if cfg.get("role_name"):
            self.page.get_by_role("button", name=cfg["role_name"], exact=False).first.click()
            return
        if cfg.get("text"):
            self.page.get_by_text(cfg["text"], exact=False).first.click()
            return
        raise LocatorError("Botão Salvar ainda não foi mapeado")
