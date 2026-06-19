import Foundation

enum BackendSettings {
    static let baseURLKey = "backendBaseURL"
    static let defaultBaseURLString = "http://127.0.0.1:8000"

    static var configuredBaseURLString: String {
        let savedValue = UserDefaults.standard.string(forKey: baseURLKey) ?? defaultBaseURLString
        let trimmedValue = savedValue.trimmingCharacters(in: .whitespacesAndNewlines)
        return trimmedValue.isEmpty ? defaultBaseURLString : trimmedValue
    }

    static var configuredBaseURL: URL {
        URL(string: configuredBaseURLString) ?? URL(string: defaultBaseURLString)!
    }
}
