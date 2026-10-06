package edu.acme.ingest;

import java.util.Set;

public final class PackageReceiver {

    private static final Set<String> FORMATS = Set.of("SCORM", "XAPI", "VIDEO", "PDF");

    public boolean accepts(String format) {
        return format != null && FORMATS.contains(format.toUpperCase());
    }
}
