from patchright.sync_api import Page


class GetMontoDevolucion:
    @staticmethod
    def execute(page: Page) -> str:
        monto_devolucion: str = "0.00"

        monto_devolver_element = page.query_selector(".mostrarDevoMoney")
        assert monto_devolver_element

        monto_devolver_text: str = monto_devolver_element.text_content() or "S/0.00"
        monto_devolver_text = monto_devolver_text.replace("\xa0", "")
        monto_devolver_text = monto_devolver_text.strip().replace("S/", "")

        if monto_devolver_text != "0.00":
            monto_devolucion = monto_devolver_text

        return monto_devolucion
