let
    // Source PostgreSQL
    Source = try

        let

            _src = PostgreSQL.Database("postgres91.test.tsi.lan:5432", "TestV1"),

            _nav = _src{[Schema="public", Item="xy"]}[Data]

        in _nav

    otherwise

        #table({"a", "Today's Date", "x", "y"}, {}),
    #"Renamed Columns" = Table.RenameColumns(Source, {{"a", "A"}, {"x", "X"}, {"y", "Y"}}),
    Result = #"Renamed Columns"
in
    Result