let
    // Source SQL Server
    Source = try

        let

            _src = Sql.Database("superstore.sample.db", "sample_superstore"),

            _nav = _src{[Schema="dbo", Item="Orders"]}[Data]

        in _nav

    otherwise

        #table({"Row ID", "Order ID", "Order Date", "Ship Date", "Ship Mode", "Customer ID", "Customer Name", "Segment", "City", "State", "Country", "Postal Code", "Market", "Region", "Product ID", "Category", "Sub-Category", "Product Name", "Sales", "Quantity", "Discount", "Profit", "Shipping Cost", "Order Priority"}, {}),
    Result = Source
in
    Result