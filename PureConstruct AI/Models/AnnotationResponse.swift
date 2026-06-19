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

struct ApprovedFieldReference: Decodable, Identifiable {
    let id: String
    let jobId: String
    let annotationMode: AnnotationMode
    let projectId: String?
    let wallId: String?
    let reviewerId: String?
    let notes: String?
    let approvedAt: String
    let imageURL: String

    enum CodingKeys: String, CodingKey {
        case id
        case jobId = "job_id"
        case annotationMode = "annotation_mode"
        case projectId = "project_id"
        case wallId = "wall_id"
        case reviewerId = "reviewer_id"
        case notes
        case approvedAt = "approved_at"
        case imageURL = "image_url"
    }
}

struct RejectedFieldReference: Decodable, Identifiable {
    let id: String
    let jobId: String
    let annotationMode: AnnotationMode
    let projectId: String?
    let wallId: String?
    let reviewerId: String?
    let notes: String?
    let rejectedAt: String
    let imageURL: String

    enum CodingKeys: String, CodingKey {
        case id
        case jobId = "job_id"
        case annotationMode = "annotation_mode"
        case projectId = "project_id"
        case wallId = "wall_id"
        case reviewerId = "reviewer_id"
        case notes
        case rejectedAt = "rejected_at"
        case imageURL = "image_url"
    }
}
