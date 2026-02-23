from loguru import logger

from siguelo_service.entities.siguelo_entities import DetalleSeguimientoRecord

from .command import GetInfoCommand
from .get_extra_info import GetExtraInfo


class GetInfoFromRow:

    @staticmethod
    def execute(command: GetInfoCommand) -> DetalleSeguimientoRecord:
        """
        raises:
            AssertionError: when the number of paragraphs is not 6 or 7.
        """

        paragraphs: tuple[str, ...] = tuple(command.data.locator("p").all_inner_texts())
        cleaned_paragraphs: tuple[str, ...] = tuple(
            p.split(":", 1)[-1].strip() for p in paragraphs
        )
        cleaned_paragraphs_len: int = len(cleaned_paragraphs)

        assert cleaned_paragraphs_len in (6, 7)

        if cleaned_paragraphs_len == 6:
            secuence, stage, area, state, datetime, responsable = cleaned_paragraphs
        elif cleaned_paragraphs_len == 7:
            cp = cleaned_paragraphs
            secuence, stage, area, state, due_date, datetime, responsable = cp
            if due_date:
                logger.warning(f"Check this due_date: {due_date}.")
                logger.info("Idk what to do with due dates.")
        else:
            raise AssertionError

        return DetalleSeguimientoRecord(
            secuence,
            stage,
            area,
            state,
            datetime,
            responsable,
            GetExtraInfo.execute(command, state, datetime),
        )
