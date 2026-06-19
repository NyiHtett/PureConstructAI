import SwiftUI

struct GeometryOverlayView: View {
    let wallCorners: [NormalizedPoint]
    let studCenterlines: [StudCenterline]
    let floorCorners: [NormalizedPoint]
    let currentStudTop: NormalizedPoint?

    var body: some View {
        GeometryReader { proxy in
            ZStack {
                polygon(points: floorCorners, size: proxy.size)
                    .stroke(.cyan, lineWidth: 2)

                polygon(points: wallCorners, size: proxy.size)
                    .stroke(.orange, lineWidth: 2)

                ForEach(Array(wallCorners.enumerated()), id: \.offset) { index, point in
                    dot(point: point, text: "\(index + 1)", color: .orange, size: proxy.size)
                }

                ForEach(Array(floorCorners.enumerated()), id: \.offset) { index, point in
                    dot(point: point, text: "\(index + 1)", color: .cyan, size: proxy.size)
                }

                ForEach(studCenterlines) { stud in
                    Path { path in
                        path.move(to: cgPoint(stud.top, proxy.size))
                        path.addLine(to: cgPoint(stud.bottom, proxy.size))
                    }
                    .stroke(.green, lineWidth: 2)
                }

                if let currentStudTop {
                    dot(point: currentStudTop, text: "T", color: .green, size: proxy.size)
                }
            }
        }
        .allowsHitTesting(false)
    }

    private func polygon(points: [NormalizedPoint], size: CGSize) -> Path {
        Path { path in
            guard let first = points.first else { return }
            path.move(to: cgPoint(first, size))
            for point in points.dropFirst() {
                path.addLine(to: cgPoint(point, size))
            }
            if points.count >= 3 {
                path.closeSubpath()
            }
        }
    }

    private func dot(point: NormalizedPoint, text: String, color: Color, size: CGSize) -> some View {
        Text(text)
            .font(.caption.bold())
            .foregroundStyle(.black)
            .frame(width: 24, height: 24)
            .background(color, in: Circle())
            .position(cgPoint(point, size))
    }

    private func cgPoint(_ point: NormalizedPoint, _ size: CGSize) -> CGPoint {
        CGPoint(x: point.x * size.width, y: point.y * size.height)
    }
}
