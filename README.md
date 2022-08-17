# ei_figer
==== Русский ====

ei_figer - расширение для программы Blender, предназначенное для Импорта\Экспорта 3D моделей из игры Проклятые Земли.

Установка плагина происходит в разделе Edit->Preferencies, Add-ons->install... После нажатия нужно выбрать zip архив с плагином.
После установки расширения, его можно найти на 3D, рядом со вкладкой tools, вкладка EI_Tools.

Умеет следующее:
- импорт\экспорт моделей и фигур (файлы *.mod, *.lnk) из *.res файла
- импорт\экспорт анимаций (файлы *.anm) из *.res файла
- помогать с созданием морфинг компонентов.

Не умеет (планируется в будущем):
- автоматический рассчёт промежуточных компонентов морфинга модели

Краткая справка по работе с расширением.
Для импорта модели достаточно указать *.res файл, содержащий модели (поле ResFile) и указать имя модели, после чего нажать Import.
Для импорта анимации необходимо сначала загрузить модель, после чего достаточно убедиться, что указан *.res файл, ввести имя анимации (поле Name в разделе animations) и нажать Import.

Экспорт модели происходит схожим образом: нужно указать *.res файл, имя модели и нажать Export, после чего модель модель будет проверена на соответствие формату ПЗ и затем экспортируется в выбранный файл. Файл может быть уже создан, тогда модель добавится в этот файл, заменив имеющуюся. На данный момент переписывание модели сделано оптимизировано с точки зрения времязатрат записи в файл, поэтому старые данные остаются в *res файле, но прочитать их будет невозможно. Чтобы получить чистовой *.res файл, нужно его перепаковать, используя eipacker от Demoth. Найти его можно, например, здесь: https://allods.gipat.ru/index.php?p=filesei . В дальнейшем планирую добавить эту функцию в плагин (опционально).

Немного вводной информации о морфинге.
Морфинг в моделях ПЗ можно представить как набор из крайних значений/моделей, которые модель принимает при изменении параметров силы/ловкости/роста. Всего таких моделей может быть 8. Допустим, мы хотим сделать более массивную грудь у кабана, когда он становится сильным, для этого нам необходимо сделать копию базовой модели, применить к ней правки (важно! удалять/добавлять точки нельзя, можно менять только их положение), и разместить на коллекцию str (в данном случае речь идёт о коллеции в Blender). Тогда, игра будет считать разницу между этими моделями и умножать/скалировать/высчитывать исходя из заданного на карте параметра "сила" у кабана. Для простоты понимания, если сила равна 0, то модель будет выглядить как базовая, для силы, равной 1, модель будет выглядить как та, которая расположилась на коллекции str.
Когда создаётся новый объект и мы хотим сделать для него компоненты силы, ловкости и т.д., нам нужно скопировать модель для её дальнейшего редактирования. С этой целью и создана функция Copy as (находится на панели расширения в разделе operations). Она позволяет скопировать выбранные объекты как компоненты морфинга и сразу же разместить на нужной коллекции.

==== English ====

ei_figer is an addon for the Blender program, designed to Import/Export 3D models from the game Evil Islands.

The addon can be installed via the Edit->Preferences, Add-ons->install... After clicking, you need to select the zip archive with the addon.
After installing the extension, it can be found on 3D, next to the tools tab, the EI_Tools tab.

Able to the following:
- import/export of models and shapes (*.mod, *.lnk files) from *.res file
- import/export animations (*.anm files) from a *.res file
- help with the creation of morphing components.

TODO:
- automatic calculation of intermediate morphing components of the model

A brief reference on working with the extension.
To import a model, it is enough to specify the *.res file containing the models (ResFile field) and specify the model name, then click Import.
To import an animation, you must first load the model, after which it is enough to make sure that the *.res file is specified, enter the name of the animation (the Name field in the animations section) and click Import.

The model is exported in a similar way: you need to specify the *.res file, the model name and click Export, after which the model model will be checked for compliance with the EI format and then exported to the selected file. The file may have already been created, then the model will be added to this file, replacing the existing one. At the moment, the rewriting of the model has been optimized in terms of the time spent writing to the file, so the old data remains in the *res file, but it will be impossible to read them. To get a clean *.res file, you need to repack it using eipacker from Demoth. You can find it, for example, here: https://allods.gipat.ru/index.php?p=filesei . In the future, I plan to add this function to the plugin (optional).

A little introductory information about morphing.
Morphing in EI models can be represented as a set of extreme values/models that the model accepts when changing the parameters of strength/agility/growth. There may be 8 such models in total. Let's say we want to make a more massive chest of a boar when it becomes strong, for this we need to make a copy of the base model, apply edits to it (important! you can't delete/add points, you can only change their position), and place them on the 'str collection' (in this case, we are talking about a collection in Blender). Then, the game will count the difference between these models and multiply/scale/calculate based on the "strength" parameter set on the map for the boar. For ease of understanding, if the value is 0, then the model will look like the base, for a value equal to 1, the model will look like the one that is located on the 'str collection'.
When a new object is created and we want to make components of strength, dexterity, etc. for it, we need to copy the model for its further editing. For this purpose, the 'Copy as' function was created (located on the extension panel in the operations section). It allows you to copy the selected objects as morphing components and immediately place them on the desired collection.