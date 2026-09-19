class InterfaceOracleInfo extends GSInfo {
    function GetAuthor() { return "Agent Interface research"; }
    function GetName() { return "InterfaceOracle"; }
    function GetDescription() { return "Oracle calibration fixture builder; not an agent"; }
    function GetVersion() { return 1; }
    function GetDate() { return "2026-09-13"; }
    function CreateInstance() { return "InterfaceOracle"; }
    function GetShortName() { return "AIFS"; }
    function GetAPIVersion() { return "13"; }
}
RegisterGS(InterfaceOracleInfo());
