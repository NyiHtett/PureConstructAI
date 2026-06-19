import Foundation

enum AnnotationMode: String, CaseIterable, Identifiable, Codable {
    case electricalLines = "electrical_lines"
    case studLocations = "stud_locations"
    case flooringPattern = "flooring_pattern"
    case fieldNotes = "field_notes"

    var id: String { rawValue }

    var title: String {
        switch self {
        case .electricalLines: return "Electrical Lines"
        case .studLocations: return "Stud Locations"
        case .flooringPattern: return "Flooring Pattern"
        case .fieldNotes: return "Field Notes / Hold Points"
        }
    }
}
