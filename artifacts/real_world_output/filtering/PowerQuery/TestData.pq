let
    // Source SQL Server
    Source = try

        let

            _src = Sql.Database("b5dpm3ihhu.database.windows.net", "EmptyDB"),

            _nav = _src{[Schema="dbo", Item="TestData"]}[Data]

        in _nav

    otherwise

        #table({"Account Account Name", "Account Number", "Account Number Burst Out Account", "Acct Name", "Burst Out", "Burst Out Join", "Burst Out Set list", "Burst Out View", "Count JE Number", "Entity ID", "Filter", "Fiscal Year", "Flag", "Flag__copy_", "FS Line", "FS Line Burst Out Account", "Group By", "Image", "Note Line", "Note Line Burst Out Account", "Selection", "show", "Show Cycle Based", "Sub Class", "SubClass Burst Out Account", "Type", "Amount", "Amount1", "Count of Amount Calculation", "Number of Records", "Number of Records1", "Select Burst Out", "Select Transaction Analysis view", "Sum Cy", "Sum Py1", "Sum Py2", "Sum Py3", "Sum Py4", "Total Credits", "Total Debits"}, {}),
    #"Renamed Columns" = Table.RenameColumns(Source, {{"show", "Show"}}),
    #"Added BurstoutSet" = Table.AddColumn(#"Renamed Columns", "BurstoutSet", each "", type text),
    Result = #"Added BurstoutSet"
in
    Result