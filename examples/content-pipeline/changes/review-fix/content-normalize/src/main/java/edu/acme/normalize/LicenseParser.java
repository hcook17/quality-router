package edu.acme.normalize;

final class LicenseParser {

    private LicenseParser() {
    }

    static String parse(String manifest) {
        if (manifest == null) {
            throw new IllegalArgumentException("manifest missing");
        }
        for (String entry : manifest.split(";")) {
            String[] pair = entry.strip().split("=", 2);
            if (pair.length == 2 && pair[0].equals("license") && !pair[1].isBlank()) {
                return pair[1].strip();
            }
        }
        throw new IllegalArgumentException("no license entry");
    }
}
