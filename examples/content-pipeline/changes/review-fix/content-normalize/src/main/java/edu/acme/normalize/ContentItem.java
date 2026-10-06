package edu.acme.normalize;

public record ContentItem(String id, String title, String format, String legacyCode,
                          String licenseId) {
}
