#include "RaidGame.h"
#include "Components/StaticMeshComponent.h"
#include "Components/CapsuleComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "Engine/StaticMeshActor.h"
#include "Engine/DamageEvents.h"
#include "EngineUtils.h"
#include "DrawDebugHelpers.h"

ARaidDoor::ARaidDoor(){
 PrimaryActorTick.bCanEverTick=true;auto* Pivot=CreateDefaultSubobject<USceneComponent>(TEXT("Hinge"));RootComponent=Pivot;
 Leaf=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("DoorLeaf"));Leaf->SetupAttachment(Pivot);Leaf->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cube.Cube")));Leaf->SetRelativeScale3D(FVector(1.5,.09,2.4));Leaf->SetRelativeLocation(FVector(75,0,120));Leaf->SetCollisionProfileName(TEXT("BlockAll"));
 Leaf->SetMaterial(0,LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Factory/Materials/M_green.M_green")));
}
void ARaidDoor::Use(bool Key){if(Locked&&!Key)return;Locked=false;Open=!Open;}
void ARaidDoor::Tick(float Dt){Super::Tick(Dt);FRotator R=GetActorRotation();R.Yaw=FMath::FInterpTo(R.Yaw,BaseYaw+(Open?95:0),Dt,4);SetActorRotation(R);}

ARaidBullet::ARaidBullet(){PrimaryActorTick.bCanEverTick=true;RootComponent=CreateDefaultSubobject<USceneComponent>(TEXT("Projectile"));}
void ARaidBullet::Tick(float Dt){
 Super::Tick(Dt);Life-=Dt;if(Life<=0){Destroy();return;}
 // Sweep every ballistic segment. No discrete point sampling can tunnel through cover.
 int Steps=FMath::Max(1,FMath::CeilToInt(Dt/.008f));float Step=Dt/Steps;
 for(int I=0;I<Steps;I++){
  FVector A=GetActorLocation();Velocity.Z-=981*Step;FVector B=A+Velocity*Step;FHitResult Hit;FCollisionQueryParams Q;Q.AddIgnoredActor(this);Q.AddIgnoredActor(GetOwner());
  if(GetWorld()->LineTraceSingleByChannel(Hit,A,B,ECC_Visibility,Q)){
   if(AActor* Target=Hit.GetActor())UGameplayStatics::ApplyPointDamage(Target,Damage,Velocity.GetSafeNormal(),Hit,GetInstigatorController(),this,UDamageType::StaticClass());
   DrawDebugPoint(GetWorld(),Hit.ImpactPoint,3,FColor(210,190,140),false,.25f);Destroy();return;
  }SetActorLocation(B);
 }
}

ARaidGuard::ARaidGuard(){
 PrimaryActorTick.bCanEverTick=true;GetCapsuleComponent()->InitCapsuleSize(34,90);
 BodyVisual=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Body"));BodyVisual->SetupAttachment(RootComponent);BodyVisual->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Cylinder.Cylinder")));BodyVisual->SetRelativeScale3D(FVector(.52,.42,1.15));BodyVisual->SetRelativeLocation(FVector(0,0,-12));BodyVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);BodyVisual->SetMaterial(0,LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Factory/Materials/M_green.M_green")));
 HeadVisual=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Head"));HeadVisual->SetupAttachment(RootComponent);HeadVisual->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Engine/BasicShapes/Sphere.Sphere")));HeadVisual->SetRelativeScale3D(FVector(.32,.30,.34));HeadVisual->SetRelativeLocation(FVector(0,0,63));HeadVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);HeadVisual->SetMaterial(0,LoadObject<UMaterialInterface>(nullptr,TEXT("/Game/Factory/Materials/M_dark.M_dark")));
 WeaponVisual=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Weapon"));WeaponVisual->SetupAttachment(RootComponent);WeaponVisual->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Game/Weapons/Rifle/Meshes/SM_Rifle.SM_Rifle")));WeaponVisual->SetRelativeLocation(FVector(25,10,30));WeaponVisual->SetCollisionEnabled(ECollisionEnabled::NoCollision);
 GetCharacterMovement()->MaxWalkSpeed=165;GetCharacterMovement()->bRunPhysicsWithNoController=true;
}
void ARaidGuard::BeginPlay(){Super::BeginPlay();Home=GetActorLocation();LastKnown=Home;NextShot=GetWorld()->GetTimeSeconds()+3;}
void ARaidGuard::Tick(float Dt){
 Super::Tick(Dt);if(Dead)return;
 auto* P=Cast<ARaidCharacter>(UGameplayStatics::GetPlayerCharacter(this,0));if(!P||P->Ended||P->Dead)return;
 float Now=GetWorld()->GetTimeSeconds();FVector Eye=GetActorLocation()+FVector(0,0,58),Target=P->GetActorLocation()+FVector(0,0,P->bIsCrouched?20:55);FVector Delta=Target-Eye;float Distance=Delta.Size();
 FCollisionQueryParams Q;Q.AddIgnoredActor(this);FHitResult Hit;
 bool Visible=Distance<2800&&FVector::DotProduct(GetActorForwardVector(),Delta.GetSafeNormal())>.1f&&(!GetWorld()->LineTraceSingleByChannel(Hit,Eye,Target,ECC_Visibility,Q)||Hit.GetActor()==P);
 if(Visible){LastKnown=P->GetActorLocation();AlertUntil=Now+8;}
 else if(Now-P->LastNoiseTime<.25f&&Distance<3200){LastKnown=P->GetActorLocation();AlertUntil=Now+6;}
 FVector Destination=AlertUntil>Now?LastKnown:Home+FVector(FMath::Sin(Now*.1f+Home.X)*220,FMath::Cos(Now*.1f+Home.Y)*220,0);
 FVector Dir=(Destination-GetActorLocation()).GetSafeNormal2D();if(!Dir.IsNearlyZero())SetActorRotation(FMath::RInterpTo(GetActorRotation(),Dir.Rotation(),Dt,4));
 if(Visible&&Now>=NextShot){
  NextShot=Now+FMath::FRandRange(.3f,.65f);FActorSpawnParameters SP;SP.Owner=this;SP.Instigator=this;
  FVector Shot=FMath::VRandCone(Delta.GetSafeNormal(),FMath::DegreesToRadians(2.2f+Distance*.001f));auto* Bullet=GetWorld()->SpawnActor<ARaidBullet>(Eye+Shot*45,Shot.Rotation(),SP);Bullet->Velocity=Shot*76000;Bullet->Damage=31;
 }
 if(!Visible||Distance>1100){
  FHitResult Obstacle;FVector Probe=GetActorLocation()-FVector(0,0,25);
  if(GetWorld()->LineTraceSingleByChannel(Obstacle,Probe,Probe+Dir*140,ECC_Visibility,Q)){
   if(auto* Door=Cast<ARaidDoor>(Obstacle.GetActor())){if(!Door->Locked&&!Door->Open)Door->Use(false);}
   FVector Right=FVector::CrossProduct(FVector::UpVector,Dir);FHitResult Side;
   if(!GetWorld()->LineTraceSingleByChannel(Side,Probe,Probe+Right*130,ECC_Visibility,Q))Dir=Right;
   else if(!GetWorld()->LineTraceSingleByChannel(Side,Probe,Probe-Right*130,ECC_Visibility,Q))Dir=-Right;else Dir=FVector::ZeroVector;
  }AddMovementInput(Dir,.7f);
 }
}
float ARaidGuard::TakeDamage(float Amount,const FDamageEvent& Event,AController* Instigator,AActor* Causer){
 if(Dead)return 0;
 if(Event.IsOfType(FPointDamageEvent::ClassID)){auto& P=static_cast<const FPointDamageEvent&>(Event);if(P.HitInfo.ImpactPoint.Z>GetActorLocation().Z+45)Amount*=3;}
 Health-=Amount;AlertUntil=GetWorld()->GetTimeSeconds()+10;if(Causer&&Causer->GetOwner())LastKnown=Causer->GetOwner()->GetActorLocation();
 if(Health<=0){Dead=true;GetCharacterMovement()->DisableMovement();GetCapsuleComponent()->SetCollisionEnabled(ECollisionEnabled::NoCollision);BodyVisual->SetRelativeRotation(FRotator(90,0,0));BodyVisual->SetRelativeLocation(FVector(0,0,-65));HeadVisual->SetRelativeLocation(FVector(60,0,-65));WeaponVisual->SetRelativeLocation(FVector(10,30,-70));Tags={TEXT("Loot"),TEXT("Medkit")};if(auto* P=Cast<ARaidCharacter>(Instigator?Instigator->GetPawn():nullptr))P->Kills++;}
 return Amount;
}

ARaidGameMode::ARaidGameMode(){DefaultPawnClass=ARaidCharacter::StaticClass();HUDClass=ARaidHUD::StaticClass();}
void ARaidGameMode::BeginPlay(){
 Super::BeginPlay();TArray<AActor*> Markers;for(TActorIterator<AActor> It(GetWorld());It;++It)if(It->ActorHasTag(TEXT("Door"))||It->ActorHasTag(TEXT("EnemySpawn")))Markers.Add(*It);
 for(auto* M:Markers){
  if(M->ActorHasTag(TEXT("Door"))){auto* D=GetWorld()->SpawnActor<ARaidDoor>(M->GetActorLocation(),M->GetActorRotation());D->BaseYaw=M->GetActorRotation().Yaw;D->Locked=M->ActorHasTag(TEXT("Locked"));M->Destroy();}
  else GetWorld()->SpawnActor<ARaidGuard>(M->GetActorLocation(),FRotator(0,FMath::FRandRange(-180,180),0));
 }
}
