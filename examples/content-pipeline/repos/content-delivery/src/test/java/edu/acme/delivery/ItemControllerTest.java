package edu.acme.delivery;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.util.Optional;
import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

class ItemControllerTest {

    @Test
    @Tag("AC-4")
    void hidesUnlicensedItems() {
        ItemController.ItemView unlicensed = new ItemController.ItemView("p1", "Intro", null);
        assertEquals(Optional.empty(), new ItemController().get(unlicensed));
    }
}
