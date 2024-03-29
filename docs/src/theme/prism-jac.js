const { Prism } = require("prism-react-renderer")

Prism.languages.jac = {
    'comment': {
        pattern: /(^|[^\\])#.*|(^|[^\\])\/\/.*|\/\*[\s\S]*?(?:\*\/|$)/,
        lookbehind: true,
        greedy: true
    },
    'string-interpolation': {
        pattern: /(?:f|fr|rf)(?:("""|''')[\s\S]*?\1|("|')(?:\\.|(?!\2)[^\\\r\n])*\2)/i,
        greedy: true,
        inside: {
            'interpolation': {
                // "{" <expression> <optional "!s", "!r", or "!a"> <optional ":" format specifier> "}"
                pattern: /((?:^|[^{])(?:\{\{)*)\{(?!\{)(?:[^{}]|\{(?!\{)(?:[^{}]|\{(?!\{)(?:[^{}])+\})+\})+\}/,
                lookbehind: true,
                inside: {
                    'format-spec': {
                        pattern: /(:)[^:(){}]+(?=\}$)/,
                        lookbehind: true
                    },
                    'conversion-option': {
                        pattern: /![sra](?=[:}]$)/,
                        alias: 'punctuation'
                    },
                    rest: null
                }
            },
            'string': /[\s\S]+/
        }
    },
    'triple-quoted-string': {
        pattern: /(?:[rub]|br|rb)?("""|''')[\s\S]*?\1/i,
        greedy: true,
        alias: 'string'
    },
    'string': {
        pattern: /(?:[rub]|br|rb)?("|')(?:\\.|(?!\1)[^\\\r\n])*\1/i,
        greedy: true
    },
    'function': {
        pattern: /(\b(can)\s+)\w+/g,
        lookbehind: true
    },
    'class-name': {
        pattern: /(\b(object|node|edge|walker|global|test|with)\s+)(\w+(?:(:\s*|,\s*)\w+)*)/i,
        lookbehind: true
    },
    'keyword': /\b(?:try|except|finally|raise|priv|prot|pub|object|node|edge|walker|global|test|ignore|visit|revisit|with|entry|exit|import|from|as|async|sync|assert|and|or|if|elif|else|for|to|by|while|continue|break|disengage|yield|skip|report|del|try|in|not|has|can)\b/,
    'builtin': /\b(?:str|int|float|list|tuple|set|dict|bool|bytes|any|type)\b/,
    'boolean': /\b(?:False|None|True)\b/,
    'number': /\b0(?:b(?:_?[01])+|o(?:_?[0-7])+|x(?:_?[a-f0-9])+)\b|(?:\b\d+(?:_\d+)*(?:\.(?:\d+(?:_\d+)*)?)?|\B\.\d+(?:_\d+)*)(?:e[+-]?\d+(?:_\d+)*)?j?(?!\w)/i,
    'operator': /<\||\|>|\?:|\?|:\+:|:g:|:global:|:h:|:here:|:v:|:visitor:|:w:|:walker:|:n:|:node:|:e:|:edge:|:o:|:object:|:c:|:can:|spawn|::>|<--|-->|<-->|<-\[|\]-|-\[|]->|<\+\+|\+\+>|<\+\+\>|<\+\[|\]\+|\+\[|\]\+>|&&|\|\||!|==|=|\+=|-=|\*=|\/=|:=|&|<|>|<=|>=|!=|,|\+|-|\*|\/|%|\^/,
    'punctuation': /\(|\)|\[|\]|\{|\}|;|\.:|:/
};

Prism.languages.jac['string-interpolation'].inside['interpolation'].inside.rest = Prism.languages.jac;

Prism.languages.jac = Prism.languages.jac;

