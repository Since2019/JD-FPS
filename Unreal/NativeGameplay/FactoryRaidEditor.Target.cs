using UnrealBuildTool;
public class FactoryRaidEditorTarget : TargetRules {
 public FactoryRaidEditorTarget(TargetInfo Target):base(Target){Type=TargetType.Editor;DefaultBuildSettings=BuildSettingsVersion.V7;IncludeOrderVersion=EngineIncludeOrderVersion.Unreal5_8;ExtraModuleNames.Add("FactoryRaid");}
}
