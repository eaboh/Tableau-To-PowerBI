let
    // TODO: Configure the data source for connector type: SALESFORCE
    // Replace the sample table below with the actual source expression.
    Source = Table.PromoteHeaders(Csv.Document(File.Contents(DataFolder & "\Account Owned By.csv"), [Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.Csv]), [PromoteAllScalars=true])
in
    Source