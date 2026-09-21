#include "RaidGame.h"
#include "Engine/Canvas.h"
#include "Engine/Engine.h"
#include "GameFramework/PlayerController.h"
#include "Kismet/GameplayStatics.h"

void ARaidHUD::Text(const FString& S,float X,float Y,FLinearColor C,float Scale){DrawText(S,C,X,Y,GEngine->GetMediumFont(),Scale);}
void ARaidHUD::DrawHUD(){
 Super::DrawHUD();auto* P=Cast<ARaidCharacter>(GetOwningPawn());if(!P||!Canvas)return;
 float W=Canvas->SizeX,H=Canvas->SizeY,Now=GetWorld()->GetTimeSeconds();
 if(P->Ended){DrawRect(FLinearColor(0.015f,.02f,.018f,.91f),0,0,W,H);Text(TEXT("FACTORY / RAID REPORT"),W*.23f,H*.28f,FLinearColor(.68f,.73f,.65f),1.7f);Text(P->Result,W*.23f,H*.40f,FLinearColor::White,1.3f);Text(FString::Printf(TEXT("Time %02d:%02d     Eliminations %d     Carried items %d"),int(Now-P->RaidStart)/60,int(Now-P->RaidStart)%60,P->Kills,P->Pack.Num()),W*.23f,H*.50f);Text(TEXT("ENTER / Deploy again"),W*.23f,H*.65f);return;}
 int Rem=FMath::Max(0,1200-int(Now-P->RaidStart));Text(FString::Printf(TEXT("FACTORY    %02d:%02d"),Rem/60,Rem%60),W-240,32,FLinearColor(.76f,.8f,.7f));
 DrawRect(FLinearColor(0,0,0,.65f),35,H-65,205,24);DrawRect(FLinearColor(.55f,.65f,.39f,.85f),39,H-61,P->Stamina*1.95f,5);DrawRect(FLinearColor(.75f,.74f,.58f,.85f),39,H-51,P->ArmStamina*1.95f,4);
 Text(FString::Printf(TEXT("%.1f kg   %s"),P->Weight(),P->Prone?TEXT("PRONE"):P->bIsCrouched?TEXT("CROUCH"):P->Sprinting?TEXT("SPRINT"):TEXT("WALK")),35,H-100,FLinearColor(.7f,.73f,.66f),.85f);
 if(P->Bleeding>0)Text(TEXT("BLEEDING  /  5 bandage"),35,H-133,FLinearColor(.8f,.24f,.17f));
 if(!P->Action.IsEmpty()){Text(P->Action,W*.42f,H*.72f);float Left=FMath::Max(0.f,P->ActionEnd-Now);Text(FString::Printf(TEXT("%.1f s"),Left),W*.48f,H*.76f);}
 if(Now<P->MessageUntil)Text(P->Message,35,H-165,FLinearColor(.83f,.83f,.71f),.95f);
 if(!P->ExitName.IsEmpty()){Text(TEXT("EXTRACTING / ")+P->ExitName,W*.4f,80,FLinearColor(.5f,.9f,.5f));Text(FString::Printf(TEXT("%.1f"),7-P->ExtractTime),W*.48f,115);}
 if(!P->Inventory)return;
 DrawRect(FLinearColor(.015f,.022f,.022f,.95f),W*.09f,H*.1f,W*.82f,H*.78f);
 Text(TEXT("EQUIPMENT     /     HEALTH     /     BACKPACK"),W*.13f,H*.14f,FLinearColor(.8f,.83f,.71f),1.25f);
 const TCHAR* Names[]={TEXT("HEAD"),TEXT("THORAX"),TEXT("STOMACH"),TEXT("LEFT ARM"),TEXT("RIGHT ARM"),TEXT("LEFT LEG"),TEXT("RIGHT LEG")};
 for(int I=0;I<7;I++){float Y=H*.24f+I*38;Text(Names[I],W*.13f,Y,FLinearColor(.65f,.67f,.6f),.85f);DrawRect(FLinearColor(.12f,.14f,.13f),W*.25f,Y+7,130,8);DrawRect(P->HP[I]>0?FLinearColor(.47f,.59f,.35f):FLinearColor(.5f,.1f,.1f),W*.25f,Y+7,130*P->HP[I]/P->MaxHP[I],8);Text(FString::Printf(TEXT("%.0f / %.0f"),P->HP[I],P->MaxHP[I]),W*.36f,Y,FLinearColor::White,.8f);}
 Text(FString::Printf(TEXT("Armor %.0f    Magazines %d    Loose rounds %d"),P->Armor,P->SpareMags.Num(),P->Loose),W*.13f,H*.65f,FLinearColor(.7f,.73f,.66f),.9f);
 float X0=W*.49f,Y0=H*.25f,Cell=FMath::Min(W*.052f,H*.083f);
 for(int Y=0;Y<5;Y++)for(int X=0;X<6;X++)DrawRect(FLinearColor(.11f,.14f,.13f),X0+X*Cell,Y0+Y*Cell,Cell-2,Cell-2);
 for(int N=0;N<P->Pack.Num();N++){auto& I=P->Pack[N];DrawRect(N==P->SelectedItem?FLinearColor(.34f,.38f,.23f):FLinearColor(.20f,.25f,.22f),X0+I.X*Cell+2,Y0+I.Y*Cell+2,I.W*Cell-6,I.H*Cell-6);Text(I.Name.Left(11),X0+I.X*Cell+5,Y0+I.Y*Cell+10,FLinearColor(.9f,.9f,.8f),.65f);}
 Text(TEXT("Down select   R rotate   Delete drop   H medkit   5 bandage"),W*.13f,H*.76f,FLinearColor(.68f,.72f,.63f),.8f);
 Text(TEXT("TAB close  /  Raid continues while inventory is open"),W*.13f,H*.81f,FLinearColor(.68f,.72f,.63f),.8f);
}
