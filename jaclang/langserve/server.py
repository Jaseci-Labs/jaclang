"""Jaclang Language Server."""

from __future__ import annotations

import threading
from typing import Optional

from jaclang.langserve.engine import JacLangServer
from jaclang.langserve.utils import debounce

import lsprotocol.types as lspt

server = JacLangServer()
analysis_thread: Optional[threading.Thread] = None
analysis_stop_event = threading.Event()


def analyze_and_publish(ls: JacLangServer, uri: str, level: int = 2) -> None:
    """Analyze and publish diagnostics."""
    global analysis_thread, analysis_stop_event

    def run_analysis() -> None:
        ls.quick_check(uri)
        ls.push_diagnostics(uri)
        if not analysis_stop_event.is_set() and level > 0:
            ls.deep_check(uri)
            ls.push_diagnostics(uri)
            if not analysis_stop_event.is_set() and level > 1:
                ls.type_check(uri)
                ls.push_diagnostics(uri)

    analysis_thread = threading.Thread(target=run_analysis)
    analysis_thread.start()


def stop_analysis() -> None:
    """Stop analysis."""
    global analysis_thread, analysis_stop_event
    if analysis_thread is not None:
        analysis_stop_event.set()
        analysis_thread.join()
        analysis_stop_event.clear()


@server.feature(lspt.TEXT_DOCUMENT_DID_OPEN)
async def did_open(ls: JacLangServer, params: lspt.DidOpenTextDocumentParams) -> None:
    """Check syntax on change."""
    stop_analysis()
    analyze_and_publish(ls, params.text_document.uri)


@server.feature(lspt.TEXT_DOCUMENT_DID_CHANGE)
@debounce(0.1)
async def did_change(
    ls: JacLangServer, params: lspt.DidChangeTextDocumentParams
) -> None:
    """Check syntax on change."""
    stop_analysis()
    analyze_and_publish(ls, params.text_document.uri)


@server.feature(lspt.TEXT_DOCUMENT_DID_SAVE)
async def did_save(ls: JacLangServer, params: lspt.DidSaveTextDocumentParams) -> None:
    """Check syntax on save."""
    stop_analysis()
    analyze_and_publish(ls, params.text_document.uri)


@server.feature(
    lspt.WORKSPACE_DID_CREATE_FILES,
    lspt.FileOperationRegistrationOptions(
        filters=[
            lspt.FileOperationFilter(pattern=lspt.FileOperationPattern("**/*.jac"))
        ]
    ),
)
async def did_create_files(ls: JacLangServer, params: lspt.CreateFilesParams) -> None:
    """Check syntax on file creation."""
    for file in params.files:
        ls.quick_check(file.uri)
        ls.push_diagnostics(file.uri)


@server.feature(
    lspt.WORKSPACE_DID_RENAME_FILES,
    lspt.FileOperationRegistrationOptions(
        filters=[
            lspt.FileOperationFilter(pattern=lspt.FileOperationPattern("**/*.jac"))
        ]
    ),
)
async def did_rename_files(ls: JacLangServer, params: lspt.RenameFilesParams) -> None:
    """Check syntax on file rename."""
    new_uris = [file.new_uri for file in params.files]
    old_uris = [file.old_uri for file in params.files]
    for i in range(len(new_uris)):
        ls.rename_module(old_uris[i], new_uris[i])
        ls.quick_check(new_uris[i])


@server.feature(
    lspt.WORKSPACE_DID_DELETE_FILES,
    lspt.FileOperationRegistrationOptions(
        filters=[
            lspt.FileOperationFilter(pattern=lspt.FileOperationPattern("**/*.jac"))
        ]
    ),
)
async def did_delete_files(ls: JacLangServer, params: lspt.DeleteFilesParams) -> None:
    """Check syntax on file delete."""
    for file in params.files:
        ls.delete_module(file.uri)


@server.feature(
    lspt.TEXT_DOCUMENT_COMPLETION,
    lspt.CompletionOptions(trigger_characters=[".", ":", ""]),
)
async def completion(
    ls: JacLangServer, params: lspt.CompletionParams
) -> lspt.CompletionList:
    """Provide completion."""
    return ls.get_completion(params.text_document.uri, params.position)


@server.feature(lspt.TEXT_DOCUMENT_FORMATTING)
def formatting(
    ls: JacLangServer, params: lspt.DocumentFormattingParams
) -> list[lspt.TextEdit]:
    """Format the given document."""
    return ls.formatted_jac(params.text_document.uri)


@server.feature(lspt.TEXT_DOCUMENT_HOVER, lspt.HoverOptions(work_done_progress=True))
def hover(
    ls: JacLangServer, params: lspt.TextDocumentPositionParams
) -> Optional[lspt.Hover]:
    """Provide hover information for the given hover request."""
    return ls.get_hover_info(params.text_document.uri, params.position)


@server.feature(lspt.TEXT_DOCUMENT_DOCUMENT_SYMBOL)
async def document_symbol(
    ls: JacLangServer, params: lspt.DocumentSymbolParams
) -> list[lspt.DocumentSymbol]:
    """Provide document symbols."""
    stop_analysis()
    analyze_and_publish(ls, params.text_document.uri)
    return ls.get_document_symbols(params.text_document.uri)


@server.feature(lspt.TEXT_DOCUMENT_DEFINITION)
async def definition(
    ls: JacLangServer, params: lspt.TextDocumentPositionParams
) -> Optional[lspt.Location]:
    """Provide definition."""
    stop_analysis()
    analyze_and_publish(ls, params.text_document.uri, level=1)
    return ls.get_definition(params.text_document.uri, params.position)


def run_lang_server() -> None:
    """Run the language server."""
    server.start_io()


if __name__ == "__main__":
    run_lang_server()
