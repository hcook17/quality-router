package edu.acme.normalize;

import java.util.Locale;

public final class Normalizer {

    public ContentItem normalize(RawPackage raw) {
        String title = raw.title() == null ? "" : raw.title().strip();
        String format = raw.format().toLowerCase(Locale.ROOT);
        return new ContentItem(raw.id(), title, format, resolveLicense(raw.manifest()));
    }

    static String resolveLicense(String manifest) {
        try {
            return LicenseParser.parse(manifest);
        } catch (IllegalArgumentException e) {
            return "UNLICENSED";
        }
    }
}
