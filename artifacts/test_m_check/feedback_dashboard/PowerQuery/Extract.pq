let
    // TODO: Configure the data source for connector type: SEMISTRUCTPASSIVESTORE-DIRECT
    // Replace the sample table below with the actual source expression.
    Source = try
        #table(
            {"Document Index (generated)", "category", "customer_id", "date", "email", "feedback_score", "feedback_text", "name", "sentiment"},
            {
                {1, "Sample 2", "Sample 3", 4, "Sample 5", 6, "Sample 7", "Sample 8", "Sample 9"},
                {2, "Sample 3", "Sample 4", 5, "Sample 6", 7, "Sample 8", "Sample 9", "Sample 10"}
            }
        )
    otherwise
        #table({"Document Index (generated)", "category", "customer_id", "date", "email", "feedback_score", "feedback_text", "name", "sentiment"}, {}),
    #"Renamed Columns" = Table.RenameColumns(Source, {{"category", "Category"}, {"customer_id", "Customer Id"}, {"date", "Date"}, {"email", "Email"}, {"feedback_score", "Feedback Score"}, {"feedback_text", "Feedback Text"}, {"name", "Name"}, {"sentiment", "Sentiment"}}),
    Result = #"Renamed Columns"
in
    Result