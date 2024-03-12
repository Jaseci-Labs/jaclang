
                using extension auth;
                using extension graphql;
                module default {
                    abstract type Node {
                        required property properties: json;
                        required property name: str;
                    }
                    abstract type Edge {
                        required property name: str;
                        required property properties: json;
                        link from_node: Node;
                        link to_node: Node;
                    }
                    type RootNode extending Node {}
                    type GenericNode extending Node {}
                    type GenericEdge extending Edge {}
                }
            