# This is a comment
#*
This is multi line comment
Many styles!
*#
"""
These are doc strings and can be used as comments
Use them to document your code
"""

import:jac .stuff;
import:py from .activity, Activity as Actvy;

node location {
    has x: int, y: int, name: str = True;
    has activities: list[Activity];
    has intro: str = "Welcome";
    has visited: int = 0;


    can record with tourist entry {
        visited+=1;
        for i in activities {
            i.duration = visitor.duration;
            if <h>.name not in visitor.passport {
                if i.name == "Hiking" {
                    for j=0 to j<3 by j+=1 {
                        i.duration += 1;
                    }
                    i.duration += 1;
                }
                visitor.passport.append(<h>.name);
               }
        }
    }
}

walker tourist {
    has duration: float = .435e-2;
    has budget: int;
    has passport: list[str];

    can make_visit with location, other exit {
        b=:g:stuff:w:tourist;
        a = spawn :g:stuff:w:tourist;
        a = spawn :w:tourist;
        a = <-[:g:edget:e:myedge|>(=a==1,b==2)]-;
        a = b +[:g:edget:e:myedge|>(a=1)]+> c;
        a = b <+[:g:edget:e:myedge|>(a=1)]+ c;
        a = here +[:g:edget:e:myedge|>(a=1)]+> spawn :g:stuff:n:tourist;
        :g:stuff:w:tourist |> here;
        report <h>.activities;
    }

    can do_something(app: int =Actvy) -> Actvy {
        app.do_something();
    }
    can do_something(app: int = Actvy, other: float = Actvy) -> Actvy {
        return app?.do_something(other);
    }

    can outside_func() -> None;
}


:walker:tourist:ability:outside_func {

}