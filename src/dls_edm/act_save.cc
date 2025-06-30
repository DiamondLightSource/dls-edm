#include <app_pkg.h>
#include <act_win.h>
#include <act_grf.h>
#include <stdio.h>
#include <crawler.h>

#define BUILD_DIR

// replacement implementation of crawlEdlFiles, run with
// env LD_PRELOAD=./act_save.so edm -crawl dummy.edl
// constructs all widgets and saves to allwidgets.edl

// static char *filepath = "%#s", BUILD_DIR;
static char *filename = BUILD_DIR + "allwidgets.edl";

int crawlEdlFiles(appContextClass *appCtx, crawlListPtr listHead)
{
  // construct window class, needed before widgets
  // see original crawlEdlFiles
  activeWindowClass *actWin = new activeWindowClass;
  actWin->create(appCtx, NULL, 0, 0, 0, 0, 0, NULL, NULL);
  actWin->ci = &appCtx->ci;
  actWin->fi = &appCtx->fi;
  FILE *fp = fopen(filename, "w");
  if (!fp)
  {
    fprintf(stderr, "failed to open file %s", filename);
    exit(1);
  }
  // 5 categories
  char *obj_types[] = {"Symbol",
                       "Monitors",
                       "Graphics",
                       "Dynamic Symbol",
                       "Controls"};
  // foreach type
  for (int n = 0; n < 5; ++n)
  {
    char *obj_type = obj_types[n];
    // foreach named object of this type
    for (char *name = actWin->obj.firstObjName(obj_type);
         name != 0;
         name = actWin->obj.nextObjName(obj_type))
    {
      // factory method constructs object by name
      activeGraphicClass *act = actWin->obj.createNew(name);
      // if success, call object save method
      if (act)
      {
        // initialize object window parent
        act->actWin = actWin;
        fprintf(fp, "# (%s)\n", actWin->obj.getNameFromClass(name));
        fprintf(fp, "object %s\n", name);
        act->save(fp);
      }
    }
  }
  fclose(fp);
  return 0;
}
