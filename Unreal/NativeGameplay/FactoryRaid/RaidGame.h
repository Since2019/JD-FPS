#pragma once
#include "CoreMinimal.h"
#include "GameFramework/Character.h"
#include "GameFramework/GameModeBase.h"
#include "GameFramework/HUD.h"
#include "GameFramework/SaveGame.h"
#include "RaidGame.generated.h"

class UCameraComponent;
class UStaticMeshComponent;
class USpotLightComponent;

USTRUCT()
struct FRaidItem {
 GENERATED_BODY()
 UPROPERTY() FString Name;
 UPROPERTY() int32 X=0;
 UPROPERTY() int32 Y=0;
 UPROPERTY() int32 W=1;
 UPROPERTY() int32 H=1;
 UPROPERTY() float Weight=.2f;
};

UCLASS()
class URaidSave:public USaveGame {
 GENERATED_BODY()
public:
 UPROPERTY() TArray<FRaidItem> Stash;
 UPROPERTY() int32 Survived=0;
};

UCLASS()
class ARaidDoor:public AActor {
 GENERATED_BODY()
public:
 ARaidDoor();
 UPROPERTY() UStaticMeshComponent* Leaf;
 bool Locked=false,Open=false;
 float BaseYaw=0;
 void Use(bool Key);
 virtual void Tick(float Delta)override;
};

UCLASS()
class ARaidBullet:public AActor {
 GENERATED_BODY()
public:
 ARaidBullet();
 FVector Velocity=FVector::ZeroVector;
 float Life=3,Damage=43;
 virtual void Tick(float Delta)override;
};

UCLASS()
class ARaidCharacter:public ACharacter {
 GENERATED_BODY()
public:
 ARaidCharacter();
 virtual void BeginPlay()override;
 virtual void Tick(float Delta)override;
 virtual void SetupPlayerInputComponent(UInputComponent* Input)override;
 virtual float TakeDamage(float Amount,const FDamageEvent& Event,AController* Instigator,AActor* Causer)override;
 UPROPERTY() UCameraComponent* Camera;
 UPROPERTY() UStaticMeshComponent* Rifle;
 UPROPERTY() USpotLightComponent* Torch;
 UPROPERTY() TArray<FRaidItem> Pack;
 float HP[7]={35,85,70,60,60,65,65};
 float MaxHP[7]={35,85,70,60,60,65,65};
 TArray<int32> SpareMags={30,30,30};
 int32 Mag=29,Chamber=1,Loose=60,Kills=0;
 float Stamina=100,ArmStamina=100,Armor=55,Bleeding=0,WalkFraction=1;
 bool Dead=false,Ended=false,Aiming=false,Sprinting=false,Firing=false,AutoFire=true,Inventory=false,Prone=false;
 float ActionEnd=0,NextShot=0,LastSprint=0,LastReload=-10,ExtractTime=0,LastNoiseTime=-100;
 float AimAlpha=0,Lean=0,Recoil=0,RaidStart=0,MessageUntil=0,LookScale=.075f;
 FVector SearchOrigin=FVector::ZeroVector;
 TWeakObjectPtr<AActor> SearchTarget;
 FString Action,Message,Result,Prompt,ExitName;
 int32 SelectedItem=0;
 float Weight()const;
 bool AddItem(const FString& Name,int32 W=1,int32 H=1,float Kg=.2f);
 bool HasKey()const;
 void HitRegion(int32 Region,float Amount);
 void Say(const FString& Text,float Seconds=3);
 void Finish(bool Survived);
 void Shoot();
 void StartFire();void StopFire();void StartAim();void StopAim();
 void MoveForward(float V);void MoveRight(float V);void Yaw(float V);void Pitch(float V);
 void StartSprint();void StopSprint();void Duck();void GoProne();void Reload();void Interact();void CancelInteract();void ToggleInventory();void Medicate();void Bandage();void ToggleMode();void CheckMag();void ToggleTorch();void LoadMag();void RestartRaid();void DropItem();void NextItem();void RotateItem();
 void CompleteAction();
};

UCLASS()
class ARaidGuard:public ACharacter {
 GENERATED_BODY()
public:
 ARaidGuard();
 UPROPERTY() UStaticMeshComponent* BodyVisual;
 UPROPERTY() UStaticMeshComponent* HeadVisual;
 UPROPERTY() UStaticMeshComponent* WeaponVisual;
 float Health=100,NextShot=0,NextDecision=0,AlertUntil=0;
 FVector LastKnown=FVector::ZeroVector,Home=FVector::ZeroVector;
 bool Dead=false;
 virtual void BeginPlay()override;
 virtual void Tick(float Delta)override;
 virtual float TakeDamage(float Amount,const FDamageEvent& Event,AController* Instigator,AActor* Causer)override;
};

UCLASS()
class ARaidHUD:public AHUD {
 GENERATED_BODY()
public:
 virtual void DrawHUD()override;
 void Text(const FString& S,float X,float Y,FLinearColor Color=FLinearColor::White,float Scale=1);
};

UCLASS()
class ARaidGameMode:public AGameModeBase {
 GENERATED_BODY()
public:
 ARaidGameMode();
 virtual void BeginPlay()override;
};
