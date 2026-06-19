import Foundation

struct AnnotationResponse: Decodable {
    let jobId: String
    let annotationMode: AnnotationMode
    let annotatedImageURL: String
    let warnings: [String]

    enum CodingKeys: String, CodingKey {
        case jobId = "job_id"
        case annotationMode = "annotation_mode"
        case annotatedImageURL = "annotated_image_url"
        case warnings
    }
}

struct ReviewResponse: Decodable {
    let jobId: String
    let status: String
    let eventType: String

    enum CodingKeys: String, CodingKey {
        case jobId = "job_id"
        case status
        case eventType = "event_type"
    }
}
