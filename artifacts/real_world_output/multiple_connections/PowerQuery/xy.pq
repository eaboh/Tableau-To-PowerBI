let
    // Source MySQL: mysql55:
    Source = try

        let

            _src = MySQL.Database("mysql55:", "testv1"),

            _nav = _src{[Schema="testv1", Item="xy"]}[Data]

        in _nav

    otherwise

        #table({"a"}, {}),
    Result = Source
in
    Result