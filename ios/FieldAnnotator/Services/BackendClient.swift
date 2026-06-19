import Foundation
import UIKit

enum BackendClientError: Error, LocalizedError {
    case invalidImage
    case invalidURL
    case badResponse(Int, String)

    var errorDescription: String? {
        switch self {
        case .invalidImage:
            return "Could not prepare the selected image."
        case .invalidURL:
            return "The backend URL is invalid."
        case .badResponse(let status, let body):
            return "Backend returned \(status): \(body)"
        }
    }
}

final class BackendClient {
    var baseURL: URL

    init(baseURL: URL? = nil) {
        self.baseURL = baseURL ?? BackendSettings.configuredBaseURL
    }

    func submitAnnotation(
        image: UIImage,
        annotationMode: AnnotationMode,
        projectId: String?,
        wallId: String?,
        notes: String?,
        calibrationPayload: CalibrationPayload?
    ) async throws -> AnnotationResponse {
        guard let imageData = image.jpegData(compressionQuality: 0.90) else {
            throw BackendClientError.invalidImage
        }

        let url = baseURL.appending(path: "/api/v1/annotations")
        let boundary = "Boundary-\(UUID().uuidString)"
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("multipart/form-data; boundary=\(boundary)", forHTTPHeaderField: "Content-Type")
        request.httpBody = try multipartBody(
            boundary: boundary,
            imageData: imageData,
            fields: [
                "annotation_mode": annotationMode.rawValue,
                "project_id": projectId ?? "",
                "wall_id": wallId ?? "",
                "notes": notes ?? "",
                "calibration_json": calibrationPayload.flatMap { payload in
                    let encoder = JSONEncoder()
                    encoder.dateEncodingStrategy = .iso8601
                    return try? String(data: encoder.encode(payload), encoding: .utf8)
                } ?? ""
            ]
        )

        let (data, response) = try await URLSession.shared.data(for: request)
        try validate(response: response, data: data)
        return try JSONDecoder().decode(AnnotationResponse.self, from: data)
    }

    func fetchAnnotatedImage(path: String) async throws -> UIImage {
        guard let url = URL(string: path, relativeTo: baseURL)?.absoluteURL else {
            throw BackendClientError.invalidURL
        }
        let (data, response) = try await URLSession.shared.data(from: url)
        try validate(response: response, data: data)
        guard let image = UIImage(data: data) else {
            throw BackendClientError.invalidImage
        }
        return image
    }

    func sendReview(jobId: String, eventType: String, reviewerId: String, notes: String?) async throws -> ReviewResponse {
        let url = baseURL.appending(path: "/api/v1/annotations/\(jobId)/review")
        var request = URLRequest(url: url)
        request.httpMethod = "POST"
        request.setValue("application/json", forHTTPHeaderField: "Content-Type")
        request.httpBody = try JSONSerialization.data(withJSONObject: [
            "event_type": eventType,
            "reviewer_id": reviewerId,
            "notes": notes ?? ""
        ])
        let (data, response) = try await URLSession.shared.data(for: request)
        try validate(response: response, data: data)
        return try JSONDecoder().decode(ReviewResponse.self, from: data)
    }

    private func multipartBody(boundary: String, imageData: Data, fields: [String: String]) throws -> Data {
        var data = Data()
        for (key, value) in fields {
            data.append("--\(boundary)\r\n")
            data.append("Content-Disposition: form-data; name=\"\(key)\"\r\n\r\n")
            data.append("\(value)\r\n")
        }
        data.append("--\(boundary)\r\n")
        data.append("Content-Disposition: form-data; name=\"image\"; filename=\"field-photo.jpg\"\r\n")
        data.append("Content-Type: image/jpeg\r\n\r\n")
        data.append(imageData)
        data.append("\r\n--\(boundary)--\r\n")
        return data
    }

    private func validate(response: URLResponse, data: Data) throws {
        guard let httpResponse = response as? HTTPURLResponse else { return }
        guard (200..<300).contains(httpResponse.statusCode) else {
            throw BackendClientError.badResponse(httpResponse.statusCode, String(data: data, encoding: .utf8) ?? "")
        }
    }
}

private extension Data {
    mutating func append(_ string: String) {
        append(Data(string.utf8))
    }
}
