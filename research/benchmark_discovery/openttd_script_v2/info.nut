class InterfaceFeasibilityInfo extends GSInfo {
    function GetAuthor() { return "Agent Interface research"; }
    function GetName() { return "InterfaceFeasibility"; }
    function GetDescription() { return "Read-only terrain/scoring smoke, not an agent"; }
    function GetVersion() { return 1; }
    function GetDate() { return "2026-09-13"; }
    function CreateInstance() { return "InterfaceFeasibility"; }
    function GetShortName() { return "AIFS"; }
    function GetAPIVersion() { return "13"; }
}
RegisterGS(InterfaceFeasibilityInfo());
