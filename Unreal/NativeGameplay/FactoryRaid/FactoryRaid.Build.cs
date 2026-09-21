using UnrealBuildTool;
public class FactoryRaid : ModuleRules {
 public FactoryRaid(ReadOnlyTargetRules Target) : base(Target) {
  PCHUsage=PCHUsageMode.UseExplicitOrSharedPCHs;
  PublicDependencyModuleNames.AddRange(new string[]{"Core","CoreUObject","Engine","InputCore","AIModule","NavigationSystem","Json","JsonUtilities"});
 }
}
