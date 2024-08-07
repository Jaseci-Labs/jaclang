import lsprotocol.types as lspt
from _typeshed import Incomplete
from jaclang.langserve.engine import JacLangServer as JacLangServer
from jaclang.settings import settings as settings

server: Incomplete

async def did_open(
    ls: JacLangServer, params: lspt.DidOpenTextDocumentParams
) -> None: ...
async def did_change(
    ls: JacLangServer, params: lspt.DidChangeTextDocumentParams
) -> None: ...
def formatting(
    ls: JacLangServer, params: lspt.DocumentFormattingParams
) -> list[lspt.TextEdit]: ...
def did_create_files(ls: JacLangServer, params: lspt.CreateFilesParams) -> None: ...
def did_rename_files(ls: JacLangServer, params: lspt.RenameFilesParams) -> None: ...
def did_delete_files(ls: JacLangServer, params: lspt.DeleteFilesParams) -> None: ...
def completion(
    ls: JacLangServer, params: lspt.CompletionParams
) -> lspt.CompletionList: ...
def hover(
    ls: JacLangServer, params: lspt.TextDocumentPositionParams
) -> lspt.Hover | None: ...
def document_symbol(
    ls: JacLangServer, params: lspt.DocumentSymbolParams
) -> list[lspt.DocumentSymbol]: ...
def definition(
    ls: JacLangServer, params: lspt.TextDocumentPositionParams
) -> lspt.Location | None: ...
def references(
    ls: JacLangServer, params: lspt.ReferenceParams
) -> list[lspt.Location]: ...
def semantic_tokens_full(
    ls: JacLangServer, params: lspt.SemanticTokensParams
) -> lspt.SemanticTokens: ...
def run_lang_server() -> None: ...
