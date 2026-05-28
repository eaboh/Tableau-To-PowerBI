let
    // Source Excel: Global Superstore.xlsx
    Source = try

        let

            _src = Excel.Workbook(File.Contents(DataFolder & "\Global Superstore.xlsx"), null, true),

            _nav = _src{[Item="Orders",Kind="Sheet"]}[Data]

        in _nav

    otherwise

        #table({"Row ID", "Order ID", "Order Date", "Ship Date", "Ship Mode", "Customer ID", "Customer Name", "Segment", "City", "State", "Country", "Postal Code", "Market", "Region", "Product ID", "Category", "Sub-Category", "Product Name", "Sales", "Quantity", "Discount", "Profit", "Shipping Cost", "Order Priority"}, {}),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Types" = Table.TransformColumnTypes(#"Promoted Headers", {
        {"Row ID", Int64.Type},
        {"Order ID", type text},
        {"Order Date", type date},
        {"Ship Date", type date},
        {"Ship Mode", type text},
        {"Customer ID", type text},
        {"Customer Name", type text},
        {"Segment", type text},
        {"City", type text},
        {"State", type text},
        {"Country", type text},
        {"Postal Code", type text},
        {"Market", type text},
        {"Region", type text},
        {"Product ID", type text},
        {"Category", type text},
        {"Sub-Category", type text},
        {"Product Name", type text},
        {"Sales", type number},
        {"Quantity", Int64.Type},
        {"Discount", type number},
        {"Profit", type number},
        {"Shipping Cost", type number},
        {"Order Priority", type text}
    }),
    #"Added Discount (bin)" = Table.AddColumn(#"Changed Types", "Discount (bin)", each [Discount], Int64.Type),
    #"Added Action (Discount (bin))" = Table.AddColumn(#"Added Discount (bin)", "Action (Discount (bin))", each Text.From([#"Discount (bin)"]), type text),
    #"Added Action (Segment)" = Table.AddColumn(#"Added Action (Discount (bin))", "Action (Segment)", each Text.From([#"Segment"]), type text),
    #"Added Action (State)" = Table.AddColumn(#"Added Action (Segment)", "Action (State)", each Text.From([#"State"]), type text),
    #"Added Action (YEAR(Order Date))" = Table.AddColumn(#"Added Action (State)", "Action (YEAR(Order Date))", each Text.From(Date.Year([#"Order Date"])), type text),
    #"Added Sub-Category (group)" = Table.AddColumn(#"Added Action (YEAR(Order Date))", "Sub-Category (group)", each if [#"Sub-Category"] = "Art" then "Miscellaneous_Office_Supplies" else if [#"Sub-Category"] = "Binders" then "Miscellaneous_Office_Supplies" else if [#"Sub-Category"] = "Envelopes" then "Miscellaneous_Office_Supplies" else if [#"Sub-Category"] = "Fasteners" then "Miscellaneous_Office_Supplies" else if [#"Sub-Category"] = "Labels" then "Miscellaneous_Office_Supplies" else if [#"Sub-Category"] = "Paper" then "Miscellaneous_Office_Supplies" else if [#"Sub-Category"] = "Supplies" then "Miscellaneous_Office_Supplies" else "Other", type text),
    Result = #"Added Sub-Category (group)"
in
    Result