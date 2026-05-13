let
    // Source Excel: nba_players.xlsx
    Source = try

        let

            _src = Excel.Workbook(File.Contents(DataFolder & "\nba_players.xlsx"), null, true),

            _nav = _src{[Item="Sheet1",Kind="Sheet"]}[Data]

        in _nav

    otherwise

        #table({"Player", "YR", "TM", "GP", "MIN", "FGM", "FGA", "FG%", "3PT%", "FT%", "OFF", "DEF", "REB", "ASST", "STL", "BLK", "TO", "PF", "PTS"}, {}),
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Types" = Table.TransformColumnTypes(#"Promoted Headers", {
        {"Player", type text},
        {"YR", Int64.Type},
        {"TM", type text},
        {"GP", Int64.Type},
        {"MIN", type number},
        {"FGM", type number},
        {"FGA", type number},
        {"FG%", type number},
        {"3PT%", type number},
        {"FT%", type number},
        {"OFF", type number},
        {"DEF", type number},
        {"REB", type number},
        {"ASST", type number},
        {"STL", type number},
        {"BLK", type number},
        {"TO", type number},
        {"PF", type number},
        {"PTS", type number}
    }),
    #"Added Action (Player)" = Table.AddColumn(#"Changed Types", "Action (Player)", each Text.From([#"Player"]), type text),
    Result = #"Added Action (Player)"
in
    Result