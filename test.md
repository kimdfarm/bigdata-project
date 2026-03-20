(venv) PS C:\Users\6-112\Desktop\bigprj>
(venv) PS C:\Users\6-112\Desktop\bigprj>

(venv) PS C:\Users\6-112\Desktop\bigprj>
(venv) PS C:\Users\6-112\Desktop\bigprj>
(venv) PS C:\Users\6-112\Desktop\bigprj> pwd

Path
----
C:\Users\6-112\Desktop\bigprj


(venv) PS C:\Users\6-112\Desktop\bigprj> ls


    디렉터리: C:\Users\6-112\Desktop\bigprj


Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
d-----      2026-03-20   오후 2:56                testfold
d-----      2026-03-20   오후 2:11                venv
-a----      2026-03-20   오후 2:39             32 .gitignore
-a----      2026-03-20   오후 3:13             10 pypp.py
-a----      2026-03-20   오후 2:39             58 README.md
-a----      2026-03-20   오후 2:39           1772 requirements.txt        
-a----      2026-03-20   오후 3:07            488 test.md


(venv) PS C:\Users\6-112\Desktop\bigprj> cd C:\Users\6-112\Desktop\bigprj\testfold
(venv) PS C:\Users\6-112\Desktop\bigprj\testfold> cd C:\Users\6-112\Desktop\bigprj
(venv) PS C:\Users\6-112\Desktop\bigprj> cd .. testfold
Set-Location : 'testfold' 인수를 허용하는 위치 매개 변수를 찾을 수 없습니
다.
위치 줄:1 문자:1
+ cd .. testfold
+ ~~~~~~~~~~~~~~
    + CategoryInfo          : InvalidArgument: (:) [Set-Location], Parame  
   terBindingException
    + FullyQualifiedErrorId : PositionalParameterNotFound,Microsoft.Power  
   Shell.Commands.SetLocationCommand

(venv) PS C:\Users\6-112\Desktop\bigprj> mkdir testfold2


    디렉터리: C:\Users\6-112\Desktop\bigprj


Mode                 LastWriteTime         Length Name
----                 -------------         ------ ----
d-----      2026-03-20   오후 3:17                testfold2


(venv) PS C:\Users\6-112\Desktop\bigprj> cat pypp.py  
print(1)
(venv) PS C:\Users\6-112\Desktop\bigprj> cp pypp.py 
cp : C:\Users\6-112\Desktop\bigprj\pypp.py 항목을 자기 자신으로 덮어쓸 수 
없습니다.
위치 줄:1 문자:1
+ cp pypp.py
+ ~~~~~~~~~~
    + CategoryInfo          : WriteError: (C:\Users\6-112\Desktop\bigprj\  
   pypp.py:String) [Copy-Item], IOException
    + FullyQualifiedErrorId : CopyError,Microsoft.PowerShell.Commands.Cop  
   yItemCommand

(venv) PS C:\Users\6-112\Desktop\bigprj> mv pypp.py
(venv) PS C:\Users\6-112\Desktop\bigprj> 