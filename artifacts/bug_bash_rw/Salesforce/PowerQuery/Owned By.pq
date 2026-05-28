let
    // TODO: Configure the data source for connector type: SALESFORCE
    // Replace the sample table below with the actual source expression.
    Source = Table.PromoteHeaders(Csv.Document(File.Contents(DataFolder & "\Owned By.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]), [PromoteAllScalars=true]),
    #"Added Days from Open" = Table.AddColumn(Source, "Days from Open", each Duration.Days(#date(2022, 04, 18) - Date.From([#"CreatedDate (Owned By)"])), Int64.Type),
    Result = #"Added Days from Open"
in
    Result