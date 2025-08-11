from telegram.ext import ConversationHandler, CallbackQueryHandler, CommandHandler, MessageHandler, filters

from bot.Handlers.admin import cmd_vacancy_add, vacancy_add_title, vacancy_add_desc, cmd_vacancy_del, \
    vacancy_del_callback, cmd_comment, cmd_export_students
from bot.Handlers.report import start, cancel, help
from bot.Handlers.vacancies import cmd_vacancies, vacancies_callback
from bot.Handlers.scalars import cmd_apply, scalar_answer, choose_field
from bot.Handlers.tables import tbl_cell_answer, tbl_callback, choose_edit_tables_callback
from bot.Handlers.doc import doc_callback, doc_edit_menu_callback
from bot.config import ASK_SCALAR, ASK_TBL_CELL, CONFIRM_TBL_ROW, CONFIRM_DOC, CHOOSE_EDIT_MENU, CHOOSE_TBL_FIELD, \
    CHOOSE_TABLE, V_ADD_TITLE, V_ADD_DESC


def register_handlers(application):
    """
    Регистрация всех обработчиков бота.
    """
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help))

    application.add_handler(CommandHandler("vacancies", cmd_vacancies))
    application.add_handler(CallbackQueryHandler(
        vacancies_callback,
        pattern=r"^vac:(page:\d+|open:\d+:\d+|back:\d+)$"
    ))

    conv = ConversationHandler(
        entry_points=[CommandHandler("apply", cmd_apply)],
        states={
            ASK_SCALAR: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, scalar_answer)
            ],
            ASK_TBL_CELL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, tbl_cell_answer)
            ],
            CONFIRM_TBL_ROW: [
                CallbackQueryHandler(tbl_callback)
            ],
            CONFIRM_DOC: [
                CallbackQueryHandler(doc_callback)
            ],
            CHOOSE_EDIT_MENU: [
                CallbackQueryHandler(doc_edit_menu_callback,
                                     pattern=r"^(edit_scalars|edit_tables|back_to_confirm)$")
            ],
            CHOOSE_TBL_FIELD: [
                CallbackQueryHandler(choose_field,
                                     pattern=r"^(fix:[^:]+|fixpage:\d+|fixnoop|back_to_confirm)$")
            ],
            CHOOSE_TABLE: [
                CallbackQueryHandler(choose_edit_tables_callback, pattern=r"^(edittbl:[^:]+|back_to_edit_menu)$")
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        name="apply_conv",
        persistent=False,
    )
    application.add_handler(conv)

    application.add_handler(ConversationHandler(
        entry_points=[CommandHandler("vacancy_add", cmd_vacancy_add)],
        states={
            V_ADD_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, vacancy_add_title)],
            V_ADD_DESC: [MessageHandler(filters.TEXT & ~filters.COMMAND, vacancy_add_desc)],
        },
        fallbacks=[],
        name="vacancy_add_conv",
        persistent=False
    ))

    # /vacancy_del — список + callback
    application.add_handler(CommandHandler("vacancy_del", cmd_vacancy_del))
    application.add_handler(CallbackQueryHandler(vacancy_del_callback, pattern=r"^vacdel_idx:\d+$"))

    application.add_handler(CommandHandler("comment", cmd_comment))
    application.add_handler(CommandHandler("export_students", cmd_export_students))