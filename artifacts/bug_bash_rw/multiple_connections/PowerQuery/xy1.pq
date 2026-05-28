let
    // Source SQL Server
    Source = try

        let

            _src = Sql.Database("mssql2012", "TestV1"),

            _nav = _src{[Schema="dbo", Item="xy1"]}[Data]

        in _nav

    otherwise

        #table({"a"}, {}),
    Result = Source
in
    Result