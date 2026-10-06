package edu.acme.normalize;

import static org.junit.jupiter.api.Assertions.assertEquals;

import org.junit.jupiter.api.Tag;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.params.ParameterizedTest;
import org.junit.jupiter.params.provider.NullSource;
import org.junit.jupiter.params.provider.ValueSource;

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
    void takesLicenseFromManifest() {
        ContentItem item = new Normalizer().normalize(
                new RawPackage("p2", "Hand Hygiene", "XAPI", "lang=en; license=CC-BY-4.0"));
        assertEquals("CC-BY-4.0", item.licenseId());
        assertEquals("LEG-p2", item.legacyCode());
    }

    @ParameterizedTest
    @Tag("AC-3")
    @NullSource
    @ValueSource(strings = {"lang=en", "license=", "license=  "})
    void unparseableLicenseMapsToUnlicensed(String manifest) {
        ContentItem item = new Normalizer().normalize(
                new RawPackage("p3", "Triage", "PDF", manifest));
        assertEquals("UNLICENSED", item.licenseId());
    }
}
