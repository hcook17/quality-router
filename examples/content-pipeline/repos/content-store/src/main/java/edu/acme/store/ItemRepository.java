package edu.acme.store;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

public final class ItemRepository {

    private final Map<String, String> titles = new HashMap<>();

    public void upsert(String id, String title) {
        titles.put(id, title);
    }

    public Optional<String> title(String id) {
        return Optional.ofNullable(titles.get(id));
    }
}
