package edu.acme.normalize;

import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;

import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;

class NormalizerTest {

    @Test
    @Tag("AC-1")
    void trimsTitles() {
        ContentItem item = new Normalizer().normalize(
                new RawPackage("p1", "  Intro to Sterile Technique ", "SCORM", "license=CC-BY"));
        assertEquals("Intro to Sterile Technique", item.title());
        assertEquals("scorm", item.format());
    }

    @Test
    @Tag("AC-2")
    void addsLicense() {
        ContentItem item = new Normalizer().normalize(
                new RawPackage("p2", "Hand Hygiene", "XAPI", "license=CC-BY-4.0"));
        assertNotNull(item.licenseId());
    }
}
