package edu.acme.ingest;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Test;

class PackageReceiverTest {

    @Test
    void acceptsKnownFormatsCaseInsensitively() {
        assertEquals(true, new PackageReceiver().accepts("scorm"));
        assertEquals(false, new PackageReceiver().accepts("docx"));
    }
}
