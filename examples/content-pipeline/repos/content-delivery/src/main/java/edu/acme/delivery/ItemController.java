package edu.acme.delivery;

import java.util.Optional;

public final class ItemController {

    public record ItemView(String id, String title, String licenseId) {
    }

    public Optional<ItemView> get(ItemView stored) {
        if (stored == null || stored.licenseId() == null) {
            return Optional.empty();
        }
        return Optional.of(stored);
    }
}
