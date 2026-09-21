#include "RaidGame.h"
#include "Camera/CameraComponent.h"
#include "Components/CapsuleComponent.h"
#include "Components/StaticMeshComponent.h"
#include "Components/SpotLightComponent.h"
#include "GameFramework/CharacterMovementComponent.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"
#include "EngineUtils.h"
#include "Engine/DamageEvents.h"
#include "DrawDebugHelpers.h"
#include "InputCoreTypes.h"

ARaidCharacter::ARaidCharacter(){
 PrimaryActorTick.bCanEverTick=true;
 GetCapsuleComponent()->InitCapsuleSize(34,90);
 Camera=CreateDefaultSubobject<UCameraComponent>(TEXT("Eyes"));Camera->SetupAttachment(GetCapsuleComponent());Camera->SetRelativeLocation(FVector(0,0,70));Camera->bUsePawnControlRotation=true;Camera->FieldOfView=90;
 Rifle=CreateDefaultSubobject<UStaticMeshComponent>(TEXT("Rifle"));Rifle->SetupAttachment(Camera);Rifle->SetCollisionEnabled(ECollisionEnabled::NoCollision);Rifle->SetCastShadow(false);
 Rifle->SetStaticMesh(LoadObject<UStaticMesh>(nullptr,TEXT("/Game/Weapons/Rifle/Meshes/SM_Rifle.SM_Rifle")));
 Rifle->SetRelativeLocation(FVector(25,14,-19));
 Torch=CreateDefaultSubobject<USpotLightComponent>(TEXT("WeaponLight"));Torch->SetupAttachment(Camera);Torch->SetRelativeLocation(FVector(35,7,-5));Torch->SetIntensity(15000);Torch->AttenuationRadius=2400;Torch->InnerConeAngle=13;Torch->OuterConeAngle=24;Torch->SetVisibility(false);
 auto* Move=GetCharacterMovement();Move->MaxWalkSpeed=290;Move->MaxAcceleration=900;Move->BrakingDecelerationWalking=650;Move->GroundFriction=3;Move->JumpZVelocity=340;Move->AirControl=.12f;Move->GetNavAgentPropertiesRef().bCanCrouch=true;Move->MaxWalkSpeedCrouched=120;
}

void ARaidCharacter::BeginPlay(){
 Super::BeginPlay();RaidStart=GetWorld()->GetTimeSeconds();
 AddItem(TEXT("Medkit"),2,1,.6f);AddItem(TEXT("Bandage"),1,1,.1f);
 Say(TEXT("FACTORY / Offline raid. F search or door. O extracts. Tab gear."),10);
}

void ARaidCharacter::SetupPlayerInputComponent(UInputComponent* I){
 Super::SetupPlayerInputComponent(I);
 I->BindAxis("Forward",this,&ARaidCharacter::MoveForward);I->BindAxis("Right",this,&ARaidCharacter::MoveRight);I->BindAxis("Turn",this,&ARaidCharacter::Yaw);I->BindAxis("Look",this,&ARaidCharacter::Pitch);
 I->BindKey(EKeys::LeftMouseButton,IE_Pressed,this,&ARaidCharacter::StartFire);I->BindKey(EKeys::LeftMouseButton,IE_Released,this,&ARaidCharacter::StopFire);
 I->BindKey(EKeys::RightMouseButton,IE_Pressed,this,&ARaidCharacter::StartAim);I->BindKey(EKeys::RightMouseButton,IE_Released,this,&ARaidCharacter::StopAim);
 I->BindKey(EKeys::LeftShift,IE_Pressed,this,&ARaidCharacter::StartSprint);I->BindKey(EKeys::LeftShift,IE_Released,this,&ARaidCharacter::StopSprint);
 I->BindKey(EKeys::SpaceBar,IE_Pressed,this,&ACharacter::Jump);
 I->BindKey(EKeys::C,IE_Pressed,this,&ARaidCharacter::Duck);I->BindKey(EKeys::X,IE_Pressed,this,&ARaidCharacter::GoProne);
 I->BindKey(EKeys::R,IE_Pressed,this,&ARaidCharacter::Reload);I->BindKey(EKeys::F,IE_Pressed,this,&ARaidCharacter::Interact);I->BindKey(EKeys::F,IE_Released,this,&ARaidCharacter::CancelInteract);
 I->BindKey(EKeys::Tab,IE_Pressed,this,&ARaidCharacter::ToggleInventory);I->BindKey(EKeys::H,IE_Pressed,this,&ARaidCharacter::Medicate);I->BindKey(EKeys::Four,IE_Pressed,this,&ARaidCharacter::Medicate);
 I->BindKey(EKeys::Five,IE_Pressed,this,&ARaidCharacter::Bandage);I->BindKey(EKeys::B,IE_Pressed,this,&ARaidCharacter::ToggleMode);I->BindKey(EKeys::T,IE_Pressed,this,&ARaidCharacter::ToggleTorch);I->BindKey(EKeys::P,IE_Pressed,this,&ARaidCharacter::LoadMag);
 I->BindKey(EKeys::Enter,IE_Pressed,this,&ARaidCharacter::RestartRaid);I->BindKey(EKeys::Delete,IE_Pressed,this,&ARaidCharacter::DropItem);I->BindKey(EKeys::Down,IE_Pressed,this,&ARaidCharacter::NextItem);I->BindKey(EKeys::R,IE_Released,this,&ARaidCharacter::RotateItem);
}

float ARaidCharacter::Weight()const{float W=15.f;for(auto& I:Pack)W+=I.Weight;W+=(Mag+Chamber+Loose)*.012f;for(int N:SpareMags)W+=.25f+N*.012f;return W;}
bool ARaidCharacter::HasKey()const{for(auto& I:Pack)if(I.Name==TEXT("Factory key"))return true;return false;}
bool ARaidCharacter::AddItem(const FString& Name,int32 W,int32 H,float Kg){
 for(int Y=0;Y<=5-H;Y++)for(int X=0;X<=6-W;X++){
  bool Free=true;for(auto& I:Pack)if(X<I.X+I.W&&X+W>I.X&&Y<I.Y+I.H&&Y+H>I.Y){Free=false;break;}
  if(Free){FRaidItem I;I.Name=Name;I.W=W;I.H=H;I.X=X;I.Y=Y;I.Weight=Kg;Pack.Add(I);return true;}
 }return false;
}
void ARaidCharacter::MoveForward(float V){if(!Dead&&!Ended&&!Inventory)AddMovementInput(FRotationMatrix(FRotator(0,GetControlRotation().Yaw,0)).GetUnitAxis(EAxis::X),V);}
void ARaidCharacter::MoveRight(float V){if(!Dead&&!Ended&&!Inventory)AddMovementInput(FRotationMatrix(FRotator(0,GetControlRotation().Yaw,0)).GetUnitAxis(EAxis::Y),V);}
void ARaidCharacter::Yaw(float V){if(!Dead&&!Ended&&!Inventory)AddControllerYawInput(V*(Aiming?.045f:LookScale));}
void ARaidCharacter::Pitch(float V){if(!Dead&&!Ended&&!Inventory)AddControllerPitchInput(V*(Aiming?.045f:LookScale));}
void ARaidCharacter::StartFire(){if(Inventory||Ended||Dead)return;Firing=true;Shoot();}
void ARaidCharacter::StopFire(){Firing=false;}
void ARaidCharacter::StartAim(){if(!Inventory&&!Ended&&!Dead){Aiming=true;Sprinting=false;}}
void ARaidCharacter::StopAim(){Aiming=false;}
void ARaidCharacter::StartSprint(){if(!Inventory&&!Aiming&&!bIsCrouched&&!Prone&&!Dead&&!Ended&&Action.IsEmpty())Sprinting=true;}
void ARaidCharacter::StopSprint(){Sprinting=false;LastSprint=GetWorld()->GetTimeSeconds();}
void ARaidCharacter::Duck(){if(Dead||Ended)return;Prone=false;if(bIsCrouched)UnCrouch();else Crouch();StopSprint();}
void ARaidCharacter::GoProne(){if(Dead||Ended)return;Prone=!Prone;if(Prone)Crouch();else UnCrouch();StopSprint();}
void ARaidCharacter::ToggleInventory(){if(Dead||Ended)return;Inventory=!Inventory;StopFire();StopAim();StopSprint();CancelInteract();}
void ARaidCharacter::Say(const FString& S,float Sec){Message=S;MessageUntil=GetWorld()->GetTimeSeconds()+Sec;}
void ARaidCharacter::ToggleMode(){AutoFire=!AutoFire;Say(AutoFire?TEXT("AUTO"):TEXT("SEMI"));}
void ARaidCharacter::CheckMag(){Say(Mag>25?TEXT("Magazine: almost full"):Mag>15?TEXT("Magazine: more than half"):Mag>5?TEXT("Magazine: less than half"):Mag>0?TEXT("Magazine: nearly empty"):TEXT("Magazine: empty"));}
void ARaidCharacter::ToggleTorch(){auto* PC=Cast<APlayerController>(Controller);if(PC&&PC->IsInputKeyDown(EKeys::LeftAlt)){Say(Chamber?TEXT("Chamber: loaded"):TEXT("Chamber: empty"));return;}Torch->ToggleVisibility();}

void ARaidCharacter::Reload(){
 if(Inventory||Dead||Ended)return;
 auto* PC=Cast<APlayerController>(Controller);if(PC&&PC->IsInputKeyDown(EKeys::LeftAlt)){CheckMag();return;}
 float Now=GetWorld()->GetTimeSeconds();
 if(Action==TEXT("Reload")&&Now-LastReload<.35f){Action=TEXT("Quick reload");ActionEnd=Now+1.45f;Say(TEXT("Quick reload: magazine will be dropped"));return;}
 if(!Action.IsEmpty()||SpareMags.IsEmpty()){Say(TEXT("No available magazine"));return;}
 if(Mag==30&&Chamber)return;
 LastReload=Now;Action=TEXT("Reload");ActionEnd=Now+2.6f;StopSprint();StopAim();
}
void ARaidCharacter::LoadMag(){if(!Action.IsEmpty()||Loose<=0||SpareMags.IsEmpty()||Dead||Ended)return;for(int N:SpareMags)if(N<30){Action=TEXT("Pack ammunition");ActionEnd=GetWorld()->GetTimeSeconds()+.55f;return;}}
void ARaidCharacter::Medicate(){if(!Action.IsEmpty()||Dead||Ended)return;for(auto& I:Pack)if(I.Name==TEXT("Medkit")){Action=TEXT("Treat injury");ActionEnd=GetWorld()->GetTimeSeconds()+4;StopSprint();StopAim();return;}Say(TEXT("No medical kit"));}
void ARaidCharacter::Bandage(){if(!Action.IsEmpty()||Dead||Ended)return;for(auto& I:Pack)if(I.Name==TEXT("Bandage")){Action=TEXT("Bandage");ActionEnd=GetWorld()->GetTimeSeconds()+2.5f;return;}Say(TEXT("No bandage"));}

void ARaidCharacter::Interact(){
 if(!Action.IsEmpty()||Inventory||Dead||Ended)return;
 FHitResult Hit;FCollisionQueryParams Q;Q.AddIgnoredActor(this);
 FVector Eye=Camera->GetComponentLocation();GetWorld()->LineTraceSingleByChannel(Hit,Eye,Eye+Camera->GetForwardVector()*230,ECC_Visibility,Q);
 if(auto* Door=Cast<ARaidDoor>(Hit.GetActor())){if(Door->Locked&&!HasKey())Say(TEXT("Requires Factory key"));else Door->Use(HasKey());return;}
 AActor* Closest=nullptr;float Best=220;
 for(TActorIterator<AActor> It(GetWorld());It;++It){
  if(!It->ActorHasTag(TEXT("Loot"))||It->ActorHasTag(TEXT("Searched")))continue;
  float D=FVector::Dist(Eye,It->GetActorLocation());if(D>=Best)continue;
  FVector Dir=(It->GetActorLocation()-Eye).GetSafeNormal();if(FVector::DotProduct(Dir,Camera->GetForwardVector())<.8f)continue;
  FHitResult Wall;GetWorld()->LineTraceSingleByChannel(Wall,Eye,It->GetActorLocation(),ECC_Visibility,Q);
  if(Wall.bBlockingHit&&FVector::Dist(Wall.ImpactPoint,It->GetActorLocation())>65)continue;
  Closest=*It;Best=D;
 }
 if(Closest){SearchTarget=Closest;SearchOrigin=GetActorLocation();Action=TEXT("Search");ActionEnd=GetWorld()->GetTimeSeconds()+2.8f;StopAim();StopSprint();}
}
void ARaidCharacter::CancelInteract(){if(Action==TEXT("Search")){Action.Empty();SearchTarget.Reset();}}

void ARaidCharacter::CompleteAction(){
 FString Completed=Action;Action.Empty();
 if(Completed==TEXT("Reload")||Completed==TEXT("Quick reload")){
  if(SpareMags.IsEmpty())return;
  int Best=0;for(int I=1;I<SpareMags.Num();I++)if(SpareMags[I]>SpareMags[Best])Best=I;
  int NewMag=SpareMags[Best];SpareMags.RemoveAt(Best);
  if(Completed==TEXT("Reload"))SpareMags.Add(Mag);
  else{auto* Drop=GetWorld()->SpawnActor<AActor>();Drop->SetActorLocation(GetActorLocation()-FVector(0,0,60));Drop->Tags={TEXT("Loot"),FName(*FString::Printf(TEXT("Magazine:%d"),Mag))};}
  Mag=NewMag;if(!Chamber&&Mag>0){Chamber=1;Mag--;}
 }else if(Completed==TEXT("Pack ammunition")){
  for(int& N:SpareMags)if(N<30&&Loose>0){N++;Loose--;break;}
  LoadMag();
 }else if(Completed==TEXT("Treat injury")){
  int Worst=-1;float Missing=0;for(int I=0;I<7;I++)if(HP[I]>0&&MaxHP[I]-HP[I]>Missing){Missing=MaxHP[I]-HP[I];Worst=I;}
  if(Worst>=0){HP[Worst]=FMath::Min(MaxHP[Worst],HP[Worst]+65);for(int I=0;I<Pack.Num();I++)if(Pack[I].Name==TEXT("Medkit")){Pack.RemoveAt(I);break;}}
 }else if(Completed==TEXT("Bandage")){
  if(Bleeding>0){Bleeding=0;for(int I=0;I<Pack.Num();I++)if(Pack[I].Name==TEXT("Bandage")){Pack.RemoveAt(I);break;}}
 }else if(Completed==TEXT("Search")&&SearchTarget.IsValid()){
  auto* T=SearchTarget.Get();FString Item=T->Tags.Num()>2?T->Tags[2].ToString():T->Tags.Num()>1?T->Tags[1].ToString():TEXT("Supplies");
  bool Added=false;
  if(Item.StartsWith(TEXT("Magazine:"))){SpareMags.Add(FCString::Atoi(*Item.RightChop(9)));Added=true;}
  else if(Item==TEXT("步枪弹药")){Loose+=30;Added=true;}
  else{
   if(Item==TEXT("工厂紧急出口钥匙"))Item=TEXT("Factory key");else if(Item==TEXT("医疗包"))Item=TEXT("Medkit");else if(Item==TEXT("绷带"))Item=TEXT("Bandage");else if(Item==TEXT("情报文件"))Item=TEXT("Intelligence");else if(Item==TEXT("机械零件"))Item=TEXT("Machine parts");else if(Item==TEXT("电钻"))Item=TEXT("Power drill");else if(Item==TEXT("饮用水"))Item=TEXT("Water");
   Added=AddItem(Item,Item==TEXT("Power drill")?2:1,Item==TEXT("Power drill")?2:1,Item==TEXT("Power drill")?2.2f:.3f);
  }
  if(Added){T->Tags.Add(TEXT("Searched"));Say(TEXT("Found: ")+Item);}else Say(TEXT("Backpack full. Search remains available."));SearchTarget.Reset();
 }
}

void ARaidCharacter::Shoot(){
 float Now=GetWorld()->GetTimeSeconds();if(Dead||Ended||Inventory||Sprinting||Now-LastSprint<.28f||!Action.IsEmpty()||Now<NextShot)return;
 NextShot=Now+.1f;if(!Chamber){Say(TEXT("Empty chamber / R reload"),1);return;}
 FVector Eye=Camera->GetComponentLocation(),Dir=Camera->GetForwardVector();FHitResult Wall;FCollisionQueryParams Q;Q.AddIgnoredActor(this);
 if(GetWorld()->LineTraceSingleByChannel(Wall,Eye,Eye+Dir*75,ECC_Visibility,Q)){Say(TEXT("Muzzle obstructed"),1);return;}
 Chamber=0;if(Mag>0){Mag--;Chamber=1;}
 const float Spread=FMath::DegreesToRadians(Aiming?.18f:1.4f)+GetVelocity().Size()*.000025f;
 Dir=FMath::VRandCone(Dir,Spread);
 FActorSpawnParameters SP;SP.Owner=this;SP.Instigator=this;
 auto* Bullet=GetWorld()->SpawnActor<ARaidBullet>(Eye+Dir*42,Dir.Rotation(),SP);Bullet->Velocity=Dir*88000;
 LastNoiseTime=Now;Recoil+=1.25f;AddControllerPitchInput(-.65f);AddControllerYawInput(FMath::FRandRange(-.22f,.22f));
 DrawDebugPoint(GetWorld(),Eye+Dir*85+Camera->GetRightVector()*7,13,FColor(255,195,95),false,.035f);
}

void ARaidCharacter::HitRegion(int Region,float Amount){
 if(Dead||Ended)return;Region=FMath::Clamp(Region,0,6);
 if((Region==1||Region==2)&&Armor>0){float Stopped=FMath::Min(Amount*.55f,Armor);Armor=FMath::Max(0.f,Armor-Amount*.55f);Amount-=Stopped;}
 if(HP[Region]<=0){for(int I=0;I<7;I++)if(HP[I]>0)HP[I]=FMath::Max(0.f,HP[I]-Amount/6.f);}
 else HP[Region]=FMath::Max(0.f,HP[Region]-Amount);
 if(Amount>18)Bleeding=FMath::Min(3.f,Bleeding+.5f);
 if(HP[0]<=0||HP[1]<=0){Dead=true;Finish(false);}
}
float ARaidCharacter::TakeDamage(float Amount,const FDamageEvent& Event,AController* Instigator,AActor* Causer){
 int Region=1;if(Event.IsOfType(FPointDamageEvent::ClassID)){auto& Point=static_cast<const FPointDamageEvent&>(Event);float Z=Point.HitInfo.ImpactPoint.Z-(GetActorLocation().Z-GetCapsuleComponent()->GetScaledCapsuleHalfHeight());Region=Z>155?0:Z>115?1:Z>85?2:(Point.HitInfo.ImpactPoint.Y>GetActorLocation().Y?5:6);}
 HitRegion(Region,Amount);return Amount;
}

void ARaidCharacter::Tick(float Dt){
 Super::Tick(Dt);if(Dead||Ended)return;const float Now=GetWorld()->GetTimeSeconds();auto* PC=Cast<APlayerController>(Controller);
 if(Sprinting&&(Stamina<1||bIsCrouched||Prone||Inventory))StopSprint();
 if(Sprinting&&GetVelocity().Size2D()>50){Stamina=FMath::Max(0.f,Stamina-Dt*(13+Weight()*.12f));LastSprint=Now;}else if(Now-LastSprint>1.3f)Stamina=FMath::Min(100.f,Stamina+Dt*12);
 ArmStamina=FMath::Clamp(ArmStamina+Dt*(Aiming?-7.f:13.f),0.f,100.f);
 if(PC){if(PC->WasInputKeyJustPressed(EKeys::MouseScrollUp))WalkFraction=FMath::Min(1.f,WalkFraction+.1f);if(PC->WasInputKeyJustPressed(EKeys::MouseScrollDown))WalkFraction=FMath::Max(.2f,WalkFraction-.1f);if(PC->WasInputKeyJustPressed(EKeys::O))Say(TEXT("Gate 3: open | Gate 0, Cellars: Factory key | hold zone 7 seconds"),7);}
 float Injury=(HP[5]<=0||HP[6]<=0)?.5f:1;float Load=FMath::Clamp(1-(Weight()-25)*.015f,.45f,1.f);
 GetCharacterMovement()->MaxWalkSpeed=(Sprinting?535:Prone?65:Aiming?180:290*WalkFraction)*Load*Injury;
 GetCharacterMovement()->MaxWalkSpeedCrouched=Prone?65:120*Load*Injury;
 AimAlpha=FMath::FInterpTo(AimAlpha,Aiming?1.f:0.f,Dt,7);Camera->SetFieldOfView(FMath::Lerp(90.f,62.f,AimAlpha));
 float WantLean=PC&&!Inventory?((PC->IsInputKeyDown(EKeys::E)?1:0)-(PC->IsInputKeyDown(EKeys::Q)?1:0))*18.f:0;
 FHitResult LeanHit;FCollisionQueryParams Query;Query.AddIgnoredActor(this);FVector Head=GetActorLocation()+FVector(0,0,bIsCrouched?30:70);
 if(GetWorld()->SweepSingleByChannel(LeanHit,Head,Head+GetActorRightVector()*WantLean,FQuat::Identity,ECC_Visibility,FCollisionShape::MakeSphere(10),Query))WantLean=0;
 Lean=FMath::FInterpTo(Lean,WantLean,Dt,9);Camera->SetRelativeLocation(FVector(0,Lean,Prone?-25.f:70.f));
 Recoil=FMath::FInterpTo(Recoil,0,Dt,8);
 bool Hold=PC&&PC->IsInputKeyDown(EKeys::LeftAlt)&&Aiming&&ArmStamina>0;
 float Sway=(Hold?.06f:ArmStamina<5?.9f:.25f)*FMath::Sin(Now*2.1f);
 Rifle->SetRelativeLocation(FMath::Lerp(FVector(25,14,-19),FVector(25,0,-10),AimAlpha)+FVector(-Recoil*.9f,0,Sway));
 Rifle->SetRelativeRotation(FRotator(Recoil+(Sprinting?-25:0),0,Lean*.32f+(!Action.IsEmpty()?-22:0)));
 if(Firing&&AutoFire)Shoot();
 if(Action==TEXT("Search")&&(FVector::Dist(SearchOrigin,GetActorLocation())>35||!SearchTarget.IsValid()))CancelInteract();
 if(!Action.IsEmpty()&&Now>=ActionEnd)CompleteAction();
 if(Bleeding>0){for(int I=0;I<7;I++)if(HP[I]>0)HP[I]=FMath::Max(0.f,HP[I]-Dt*Bleeding*.15f);if(HP[0]<=0||HP[1]<=0){Dead=true;Finish(false);return;}}
 ExitName.Empty();for(TActorIterator<AActor> It(GetWorld());It;++It)if(It->ActorHasTag(TEXT("Extract"))){FVector D=It->GetActorLocation()-GetActorLocation();if(D.Size2D()<165&&FMath::Abs(D.Z)<130){if(It->ActorHasTag(TEXT("Key"))&&!HasKey())Say(TEXT("Extraction requires Factory key"),1);else ExitName=It->Tags[1].ToString();break;}}
 ExtractTime=ExitName.IsEmpty()?0:ExtractTime+Dt;if(ExtractTime>=7)Finish(true);
 if(Now-RaidStart>=1200)Finish(false);
}

void ARaidCharacter::Finish(bool Survived){
 if(Ended)return;Ended=true;StopFire();StopAim();StopSprint();Action.Empty();GetCharacterMovement()->StopMovementImmediately();
 if(Survived){auto* Save=Cast<URaidSave>(UGameplayStatics::LoadGameFromSlot(TEXT("FactoryStash"),0));if(!Save)Save=Cast<URaidSave>(UGameplayStatics::CreateSaveGameObject(URaidSave::StaticClass()));Save->Stash.Append(Pack);Save->Survived++;bool Saved=UGameplayStatics::SaveGameToSlot(Save,TEXT("FactoryStash"),0);Result=Saved?TEXT("SURVIVED / Loot stored"):TEXT("SURVIVED / Save failed");}
 else Result=Dead?TEXT("KILLED IN ACTION / Carried loot lost"):TEXT("MISSING IN ACTION / Raid time expired");
}
void ARaidCharacter::RestartRaid(){if(Ended)UGameplayStatics::OpenLevel(this,FName(TEXT("ClassicFactory")));}
void ARaidCharacter::DropItem(){if(!Inventory||!Pack.IsValidIndex(SelectedItem))return;FRaidItem I=Pack[SelectedItem];auto* Drop=GetWorld()->SpawnActor<AActor>();Drop->SetActorLocation(GetActorLocation()-FVector(0,0,60));Drop->Tags={TEXT("Loot"),FName(*I.Name)};Pack.RemoveAt(SelectedItem);SelectedItem=FMath::Clamp(SelectedItem,0,Pack.Num()-1);}
void ARaidCharacter::NextItem(){if(Inventory&&Pack.Num())SelectedItem=(SelectedItem+1)%Pack.Num();}
void ARaidCharacter::RotateItem(){if(!Inventory||!Pack.IsValidIndex(SelectedItem))return;auto& I=Pack[SelectedItem];if(I.X+I.H>6||I.Y+I.W>5)return;for(int N=0;N<Pack.Num();N++)if(N!=SelectedItem){auto& O=Pack[N];if(I.X<O.X+O.W&&I.X+I.H>O.X&&I.Y<O.Y+O.H&&I.Y+I.W>O.Y)return;}Swap(I.W,I.H);}
