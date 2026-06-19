import Foundation

struct NormalizedPoint: Codable, Identifiable, Equatable {
    var id = UUID()
    var x: Double
    var y: Double
    var label: String?

    enum CodingKeys: String, CodingKey {
        case x
        case y
        case label
    }
}

struct StudCenterline: Codable, Identifiable, Equatable {
    var id: String
    var top: NormalizedPoint
    var bottom: NormalizedPoint
}

struct FloorPlane: Codable, Equatable {
    var corners: [NormalizedPoint]
}

struct CalibrationPayload: Codable, Equatable {
    var imageWidth: Int
    var imageHeight: Int
    var wallCornersNorm: [NormalizedPoint]
    var studCenterlinesNorm: [StudCenterline]
    var floorPlaneNorm: FloorPlane?
    var createdAt: Date

    enum CodingKeys: String, CodingKey {
        case imageWidth = "image_width"
        case imageHeight = "image_height"
        case wallCornersNorm = "wall_corners_norm"
        case studCenterlinesNorm = "stud_centerlines_norm"
        case floorPlaneNorm = "floor_plane_norm"
        case createdAt = "created_at"
    }
}

enum GeometryNormalizer {
    static func normalizedPoint(
        tapLocation: CGPoint,
        imageSize: CGSize,
        containerSize: CGSize
    ) -> NormalizedPoint? {
        guard imageSize.width > 0, imageSize.height > 0, containerSize.width > 0, containerSize.height > 0 else {
            return nil
        }

        let scale = min(containerSize.width / imageSize.width, containerSize.height / imageSize.height)
        let displayedSize = CGSize(width: imageSize.width * scale, height: imageSize.height * scale)
        let origin = CGPoint(
            x: (containerSize.width - displayedSize.width) / 2,
            y: (containerSize.height - displayedSize.height) / 2
        )
        let imagePoint = CGPoint(x: tapLocation.x - origin.x, y: tapLocation.y - origin.y)

        guard imagePoint.x >= 0, imagePoint.y >= 0, imagePoint.x <= displayedSize.width, imagePoint.y <= displayedSize.height else {
            return nil
        }

        return NormalizedPoint(
            x: min(max(imagePoint.x / displayedSize.width, 0), 1),
            y: min(max(imagePoint.y / displayedSize.height, 0), 1),
            label: nil
        )
    }
}
