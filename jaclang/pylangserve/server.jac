"""Jaclang Language Server."""

import:py from __future__, annotations ;
import:py from typing, Optional ;
import:py from jaclang.compiler.constant, JacSemTokenModifier as SemTokMod, JacSemTokenType as SemTokType ;
import:py from jaclang.langserve.engine, JacLangServer ;
import:py from jaclang.langserve.utils, debounce ;
import:py lsprotocol.types as lspt ;

with entry {
    server = JacLangServer();
}

@ server.feature(lspt.TEXT_DOCUMENT_DID_OPEN)@server.feature(lspt.TEXT_DOCUMENT_DID_SAVE) 
 async can did_open(ls: JacLangServer, params: lspt.DidOpenTextDocumentParams) -> None {
    """Check syntax on change.""" ;    
    awaitls.analyze_and_publish(params.text_document.uri) ;
}

@ server.feature(lspt.TEXT_DOCUMENT_DID_CHANGE)@debounce(0.3) 
 async can did_change(ls: JacLangServer, params: lspt.DidOpenTextDocumentParams) -> None {
    """Check syntax on change.""" ;    
    awaitls.analyze_and_publish(params.text_document.uri, level=1) ;
}

@ server.feature(lspt.TEXT_DOCUMENT_FORMATTING) 
 can formatting(ls: JacLangServer, params: lspt.DocumentFormattingParams) -> list[lspt.TextEdit] {
    """Format the given document.""" ;    
    return ls.formatted_jac(params.text_document.uri) ;
}

@ server.feature(
    lspt.WORKSPACE_DID_CREATE_FILES,
    lspt.FileOperationRegistrationOptions(
        filters=[lspt.FileOperationFilter(
            pattern=lspt.FileOperationPattern("**/*.jac")
        )]
    )
) 
 can did_create_files(ls: JacLangServer, params: lspt.CreateFilesParams) -> None {
    """Check syntax on file creation.""" ;
}

@ server.feature(
    lspt.WORKSPACE_DID_RENAME_FILES,
    lspt.FileOperationRegistrationOptions(
        filters=[lspt.FileOperationFilter(
            pattern=lspt.FileOperationPattern("**/*.jac")
        )]
    )
) 
 can did_rename_files(ls: JacLangServer, params: lspt.RenameFilesParams) -> None {
    """Check syntax on file rename.""" ;    
    new_uris = [file.new_uri for file in params.files];    
    old_uris = [file.old_uri for file in params.files];    
    for i in range(len(new_uris)) {
        ls.rename_module(old_uris[i], new_uris[i]) ;
    }
}

@ server.feature(
    lspt.WORKSPACE_DID_DELETE_FILES,
    lspt.FileOperationRegistrationOptions(
        filters=[lspt.FileOperationFilter(
            pattern=lspt.FileOperationPattern("**/*.jac")
        )]
    )
) 
 can did_delete_files(ls: JacLangServer, params: lspt.DeleteFilesParams) -> None {
    """Check syntax on file delete.""" ;    
    for file in params.files {
        ls.delete_module(file.uri) ;
    }
}

@ server.feature(
    lspt.TEXT_DOCUMENT_COMPLETION,
    lspt.CompletionOptions(
        trigger_characters=[".", ":", "a-zA-Z0-9"]
    )
) 
 can completion(ls: JacLangServer, params: lspt.CompletionParams) -> lspt.CompletionList {
    """Provide completion.""" ;    
    return ls.get_completion(
        params.text_document.uri,
        params.position,
        params.context.trigger_character
    ) ;
}

@ server.feature(
    lspt.TEXT_DOCUMENT_HOVER,
    lspt.HoverOptions(work_done_progress=True)
) 
 can hover(ls: JacLangServer, params: lspt.TextDocumentPositionParams) -> Optional[lspt.Hover] {
    """Provide hover information for the given hover request.""" ;    
    return ls.get_hover_info(
        params.text_document.uri,
        params.position
    ) ;
}

@ server.feature(lspt.TEXT_DOCUMENT_DOCUMENT_SYMBOL) 
 can document_symbol(ls: JacLangServer, params: lspt.DocumentSymbolParams) -> list[lspt.DocumentSymbol] {
    """Provide document symbols.""" ;    
    return ls.get_document_symbols(params.text_document.uri) ;
}

@ server.feature(lspt.TEXT_DOCUMENT_DEFINITION) 
 can definition(ls: JacLangServer, params: lspt.TextDocumentPositionParams) -> Optional[lspt.Location] {
    """Provide definition.""" ;    
    return ls.get_definition(
        params.text_document.uri,
        params.position
    ) ;
}

@ server.feature(lspt.TEXT_DOCUMENT_REFERENCES) 
 can references(ls: JacLangServer, params: lspt.ReferenceParams) -> list[lspt.Location] {
    """Provide references.""" ;    
    return ls.get_references(
        params.text_document.uri,
        params.position
    ) ;
}

@ server.feature(
    lspt.TEXT_DOCUMENT_SEMANTIC_TOKENS_FULL,
    lspt.SemanticTokensLegend(
        token_types=SemTokType.as_str_list(),
        token_modifiers=SemTokMod.as_str_list()
    )
) 
 can semantic_tokens_full(ls: JacLangServer, params: lspt.SemanticTokensParams) -> lspt.SemanticTokens {
    """Provide semantic tokens.""" ;    
    return ls.get_semantic_tokens(params.text_document.uri) ;
}

can run_lang_server() -> None {
    """Run the language server.""" ;    
    server.start_io() ;
}

with entry {
    if __name__ == "__main__" {
        run_lang_server() ;} 
}

