"""Example of multiple inheritance."""

object Parent {
    can init() -> None {
        # Parent initialization
    }
    can speak() -> None {
        # Parent speaking
    }
}

object Mom:Parent {
    can init() -> None {
        # Mom initialization
        :o:Parent.init();
    }
    can speak() -> None {
        # Mom speaking
    }
}

object Dad:Parent {
    can init() -> None {
        # Dad initialization
        :o:Parent.init();
    }
    can speak() -> None {
        # Dad speaking
    }
}

object Child:Mom:Dad { #Child inherits from Mom and Dad
    can init() -> None {
        # Child initialization
        :o:Mom.init();
        :o:Dad.init();
    }
}