class InterfaceTaskInfo extends GSInfo {
    function GetAuthor() { return "Agent Interface research"; }
    function GetName() { return "InterfaceTask"; }
    function GetDescription() { return "Saved road task fixture"; }
    function GetVersion() { return 1; }
    function GetDate() { return "2026-09-13"; }
    function CreateInstance() { return "InterfaceTask"; }
    function GetShortName() { return "AIFS"; }
    function GetAPIVersion() { return "13"; }
}
RegisterGS(InterfaceTaskInfo());
