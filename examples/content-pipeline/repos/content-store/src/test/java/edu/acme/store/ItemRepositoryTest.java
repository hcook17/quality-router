package edu.acme.store;

import static org.junit.jupiter.api.Assertions.assertEquals;

import java.util.Optional;
import org.junit.jupiter.api.Test;

class ItemRepositoryTest {

    @Test
    void upsertIsIdempotent() {
        ItemRepository repo = new ItemRepository();
        repo.upsert("p1", "Intro");
        repo.upsert("p1", "Intro");
        assertEquals(Optional.of("Intro"), repo.title("p1"));
    }
}
